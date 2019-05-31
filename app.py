# -*- coding: utf-8 -*-
import base64
from urllib.parse import quote as urlquote
import os, re, json

import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output
from flask import Flask, send_from_directory

import plotly.graph_objs as go
import pandas as pd
from datetime import datetime as dt
from datetime import date, timedelta
import aux_methods as aux

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

# ------------------ AUX METHODS FOR FILE HANDLING --------------------- #
'''
Move this to aux_method.py whenever possible
'''
def save_file(name, content):
    """Decode and store a file uploaded with Plotly Dash."""
    data = content.encode("utf8").split(b";base64,")[1]
    with open(os.path.join(UPLOAD_DIRECTORY, name), "wb") as fp:
        fp.write(base64.decodebytes(data))


def uploaded_files():
    """List the files in the upload directory."""
    files = []
    for filename in os.listdir(UPLOAD_DIRECTORY):
        path = os.path.join(UPLOAD_DIRECTORY, filename)
        if os.path.isfile(path):
            files.append(filename)
    return files

# --------------------------------------------------------------------- #

UPLOAD_DIRECTORY = "./Data/"

if not os.path.exists(UPLOAD_DIRECTORY):
    os.makedirs(UPLOAD_DIRECTORY)


# Normally, Dash creates its own Flask server internally. By creating our own,
# we can create a route for downloading files directly:
server = Flask(__name__)
app = dash.Dash(server=server,external_stylesheets=external_stylesheets)

# ---------------- DASHBOARD LAYOUT -------------------------- #

# colorscheme ------------------------------------------------ #
colors = dict(darkest='#344b52', darker='#597f8a', lightest='#f5f5f5', pastel='#cfd3ca', lighter='#a1bdc2')

# HTMLish ---------------------------------------------------- #
app.layout = html.Div(style=dict(backgroundColor=colors['lightest']), children=[
    html.H2(children='Orion Dashboard', style={
        'textAlign': 'center',
    }),
    
    # invisible div to save the dataframe
    html.Div(id='dataframe', style={'display': 'none'}),

    html.Div(
        className='container',
        style=dict(
            width='30%', display='flex', backgroundColor=colors['lightest'],
            flexDirection='row', justifyContent='space-evenly',
        ),    
        children=[
            
            # Date Picker
            # hmtl.Div(
            #     children=dcc.DatePickerRange(id='date-range',display_format='D MMM, YYYY',with_portal=True,with_full_screen_portal=False)            
            # )
            dcc.DatePickerRange(
                id='date-range-picker',
                initial_visible_month=dt.today().date(),
                start_date=dt.today().date() - timedelta(days=30),
                end_date=dt.today().date(),
                display_format='D MMM, YYYY',
                with_portal=True,
                with_full_screen_portal=False,
            ),

            # Upload Button
            dcc.Upload(
                id="upload-data",
                children=html.Div(
                    ["Drop file or click to select"]
                ),
                multiple=True,
            ),

            # Reload Button
            html.Button(
                id='propagate-button',                        
                n_clicks=0,
                children=[]
            ),
        ]
    ),
    
    html.Div([
        dcc.RadioItems(
            id='radio_states',
            options=[
                {'label': 'Failure Rate', 'value': 'f_rate'},
                {'label': 'Test Points', 'value': 't_points'},
                {'label': 'Devices', 'value': 'd_specs'}
            ],
            value='f_rate',
            labelStyle={'display': 'inline-block'}
        ),
        
        dcc.Dropdown(
            id='dropdown_states',
            multi=True
        )
    ], className="row", style={'marginTop': 15, 'marginBottom': 15}),

    html.Div([
        dcc.Graph(
            id='graph1',
        ),
        
        # data display of clicked items 
        html.Pre(id='click-data'),

    ], className="row", style={'marginTop': 15, 'marginBottom': 15, 'marginLeft': 20, 'marginRight': 20}),
   
#    html.Div([
#        html.H3("File List"),
#        html.Ul(id="file-list"),    
#    ], className='column', style=dict(float='left')),
])

# ---------------- DASHBOARD INTERACTIONS ------------------------ #

@app.callback(
        [Output('date-range-picker', 'initial_visible_month'),
        Output('date-range-picker', 'start_date'),
        Output('date-range-picker', 'end_date'),
        Output('date-range-picker', 'min_date_allowed'),
        Output('date-range-picker', 'max_date_allowed')],
        [Input('dataframe', 'children')]
)
def update_datepicker(json_df):
    # sets 'created_at' as DatetimeIndex (necessary for the auxiliary methods in aux_methods.py)
    df = pd.read_json(json_df, orient='split')
    df.set_index('created_at', inplace=True)
    df.sort_index(kind='mergesort', inplace=True) 
    
    return dt(df.index.max().year, df.index.max().month, 1), df.index.max().date() - timedelta(days=15),df.index.max().date() + timedelta(days=1), df.index.min().date(), df.index.max().date() + timedelta(days=1)


@app.callback(
    dash.dependencies.Output('dropdown_states', 'options'),
    [
        Input('dataframe', 'children'),
        Input('radio_states', 'value'),
        Input('date-range-picker', 'start_date'),
        Input('date-range-picker', 'end_date'),
    ]
)
def update_dropdown_states(json_df, mode, start_date, end_date):
    '''
    '''
    # sets 'created_at' as DatetimeIndex (necessary for the auxiliary methods in aux_methods.py)
    df = pd.read_json(json_df, orient='split')
    df.set_index('created_at', inplace=True)
    df.sort_index(kind='mergesort', inplace=True) 
    
    start = dt.strptime(start_date, '%Y-%m-%d')
    end = dt.strptime(end_date, '%Y-%m-%d')

    if mode == 'f_rate':
        return [{'label': ' '.join(i.split('_')).title(), 'value': i} for i in ['passed', 'failed_1', 'failed_2', 'failed_3', 'failed_all']]
    
    elif mode == 't_points':
        return [{'label': i.title(), 'value': i} for i in ['response', 'polarity', 'rub+buzz', 'thd']]

    elif mode == 'd_specs':
        if start is not None and end is not None:
            return [{'label': i.title(), 'value': i} for i in df.loc[start : end].id.values]


@app.callback(
    dash.dependencies.Output('graph1', 'figure'),
    [
        dash.dependencies.Input('dataframe', 'children'),
        dash.dependencies.Input('date-range-picker', 'start_date'),
        dash.dependencies.Input('date-range-picker', 'end_date'),
        dash.dependencies.Input('dropdown_states', 'value'),
        dash.dependencies.Input('radio_states', 'value'),
    ]
)
def update_graph1(json_df, start_date, end_date, in_focus, mode):
    '''
    '''
    # sets 'created_at' as DatetimeIndex (necessary for the auxiliary methods in aux_methods.py)
    df = pd.read_json(json_df, orient='split')
    df.set_index('created_at', inplace=True)
    df.sort_index(kind='mergesort', inplace=True) 
    
    # transform into datetime.date object
    start = dt.strptime(start_date, '%Y-%m-%d')
    end = dt.strptime(end_date, '%Y-%m-%d')

    if mode == 'f_rate':
        return aux.update_barplot(df, start, end, in_focus)

    elif mode == 'd_specs':
        return aux.update_windroseplot(df, start, end, in_focus)


@app.callback(
    dash.dependencies.Output('click-data', 'children'),
    [ dash.dependencies.Input('graph1', 'clickData')]
)
def display_click_data(clickData):
    return json.dumps(clickData, indent=2)

#@app.callback(
#    Output("file-list", "children"),
#    [Input("upload-data", "filename"), Input("upload-data", "contents")],
#)
#def update_output(uploaded_filenames, uploaded_file_contents):
#    """Save uploaded files and regenerate the file list."""
#
#    if uploaded_filenames is not None and uploaded_file_contents is not None:
#        for name, data in zip(uploaded_filenames, uploaded_file_contents):
#            save_file(name, data)
#
#    files = uploaded_files()
#    if len(files) == 0:
#        return [html.Li('No files yet!')]
#    else:
#        return [html.Li(file_download_link(filename)) for filename in files]

@app.callback(
    Output('dataframe', 'children'),
    [Input('upload-data', 'filename'), Input('upload-data', 'contents')],
)
def parse_inputfiles(fnames_to_upload: list, fcontent_to_upload: list) -> pd.DataFrame:
    '''
    '''
    # load files in the 'tmp/' folder
    files_indisk = uploaded_files()  
    path = 'Data/'  

    if fnames_to_upload and fcontent_to_upload:
        
        for name, data in zip(fnames_to_upload, fcontent_to_upload):
            if name not in files_indisk:
                save_file(name, data)

    try:
        return aux.load_testresults_todataframe(path).to_json(date_format='iso', orient='split')
    
    except Exception as e:
        print('PARSE_INPUT_ERROR:', e)
        return pd.DataFrame().to_json(date_format='iso', orient='split')


# @app.callback(
#     dash.dependencies.Output('stats-in-daterange', 'figure'),
#     [
#         dash.dependencies.Input('categories', 'value'),
#         dash.dependencies.Input('speakers-in-daterange', 'relayoutData')
#     ])
# def update_bar_chart(categories, relayoutData):
#     if categories is None or categories == []:
#         categories = CATEGORIES

#     if (relayoutData is not None
#             and (not (relayoutData.get('xaxis.autorange') or relayoutData.get('yaxis.autorange')))):
#         x0 = dateutil.parser.parse(relayoutData['xaxis.range[0]'])
#         x1 = dateutil.parser.parse(relayoutData['xaxis.range[1]'])
#         y0 = 10 ** relayoutData['yaxis.range[0]']
#         y1 = 10 ** relayoutData['yaxis.range[1]']

#         sub_df = orion_df[orion_df.created_at.between(x0, x1) & orion_df.usd_pledged.between(y0, y1)]
#     else:
#         sub_df = orion_df

#     stacked_barchart_df = (
#         sub_df[sub_df['broader_category'].isin(categories)]['state'].groupby(sub_df['broader_category'])
#         .value_counts(normalize=False)
#         .rename('count')
#         .to_frame()
#         .reset_index('state')
#         .pivot(columns='state')
#         .reset_index()
#     )
#     return {
#         'data': [
#             go.Bar(
#                 x=stacked_barchart_df['broader_category'],
#                 y=stacked_barchart_df['count'][state],
#                 name=state,
#                 marker={
#                     'color': color
#                 }
#             ) for (state, color) in zip(STATES[::-1], COLORS[::-1])
#         ],
#         'layout': go.Layout(
#             yaxis={'title': 'Number of projects'},
#             barmode='stack',
#             hovermode='closest'
#         )
#     }


# ---------------- MAIN ------------------------ #

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    #debug = os.environ.get('PRODUCTION') is None
    app.run_server(debug=True, host='0.0.0.0', port=port)
