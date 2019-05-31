# -*- coding: utf-8 -*-
import base64
from urllib.parse import quote as urlquote
import os, re, json

import dash, dash_table
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output, State
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
app.config['suppress_callback_exceptions'] = True

# ---------------- DASHBOARD LAYOUT -------------------------- #

# custom layout ---------------------------------------------- #
app.index_string = '''
<!DOCTYPE html>
<html>
    <head>
        <title>{%title%}</title>
        {%favicon%}
        {%css%}
    </head>
    <body>
        {%app_entry%}
        <footer>
            {%config%}
            {%scripts%}
            {%renderer%}
        </footer>
        <hr>
        <div>Copyright (C) 2019  Otto von Sperling under GPLv3</div>
    </body>
</html>
'''

# colorscheme ------------------------------------------------ #
colors = dict(darkest='#344b52', darker='#597f8a', lightest='#f5f5f5', pastel='#cfd3ca', lighter='#a1bdc2')

# HTMLish ---------------------------------------------------- #
app.layout = html.Div(style=dict(backgroundColor=colors['lightest']), children=[
    html.Div(
        className='container',
        style=dict(display='flex', justifyContent='center'),
        children=[
            html.Img(src='/assets/favicon.ico', style=dict(height='50px', marginTop='2%', marginRight='10px')),
            html.H2(children='Orion Dashboard', style=dict(textAlign='center', marginTop='2.2%')),
        ]
    ),
    
    # invisible div to save the dataframe
    html.Div(id='dataframe', style={'display': 'none'}),

    html.Div(
        className='3 rows',
        style=dict(backgroundColor=colors['lightest']),    
        children=[
            
            # Date Picker
            # hmtl.Div(
            #     children=dcc.DatePickerRange(id='date-range',display_format='D MMM, YYYY',with_portal=True,with_full_screen_portal=False)            
            # )
            dcc.DatePickerRange(
                id='date-range-picker',
                style=dict(backgroundColor=colors['lightest'], fontSize='16px'),
                initial_visible_month=dt.today(),
                start_date=dt.today().date() - timedelta(days=30),
                end_date=dt.today().date(),
                display_format='D MMM, YYYY',
                with_portal=False,
                with_full_screen_portal=False,
            ),

            # Upload Button
            dcc.Upload(
                id="upload-data",
                style=dict(
                    width='12%',
                    float="right",
                    border='1px solid gray',
                    textAlign='center',
                    # display='inline-block',
                    marginBottom='1%',
                    fontSize='14px',
                    # padding='5px 5px',
                    borderRadius='4px',

                ),
                children=html.Div(
                    ["Drop file or click to select"]
                ),
                multiple=True),
        ]
    ),
    
    html.Div(
        className='3 rows',
        style=dict(backgroundColor=colors['lightest']), 
        children=[

            dcc.RadioItems(
                id='radio-select',
                style=dict(marginTop='5px'),
                options=[
                    {'label': 'Failure Rate', 'value': 'f_rate'},
                    {'label': 'Devices', 'value': 'd_specs'}
                ],
                value='f_rate',
                labelStyle={'display': 'inline-block'}
            ),
            
            dcc.Dropdown(id='dropdown-select',multi=True)
        ]
    ),

    html.Div(
        id='main-div',
        className='3 rows container',
        style=dict(backgroundColor=colors['lightest'], display='flex', width='100%'), 
        children=[
            
            html.Div(
                id='graph-div',
                className='item',
                style=dict(
                    backgroundColor=colors['lightest'],
                    order=1,

                ),
                children=[dcc.Graph(id='graph1'),]
            ),
            
            html.Div(
                className='item',
                style=dict(
                    backgroundColor=colors['lightest'],
                    order=2,
                ), 
                children=[
                    html.Div(id='datatable-div',style=dict(display='none'),children=[dash_table.DataTable(id='datatable', data=[],columns=[{}])])]    
            ),
        ]),
    

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
    [Output('dropdown-select', 'options'),Output('dropdown-select', 'value')],
    [Input('dataframe', 'children'),Input('radio-select', 'value'),Input('date-range-picker', 'start_date'),Input('date-range-picker', 'end_date')],
    [State('dropdown-select', 'value')]
)
def update_dropdown_states(json_df, mode, start_date, end_date, previous_selection):
    '''
    '''
    if previous_selection:
        pass

    # sets 'created_at' as DatetimeIndex (necessary for the auxiliary methods in aux_methods.py)
    df = pd.read_json(json_df, orient='split')
    df.set_index('created_at', inplace=True)
    df.sort_index(kind='mergesort', inplace=True) 
    
    start = dt.strptime(start_date, '%Y-%m-%d')
    end = dt.strptime(end_date, '%Y-%m-%d')

    if mode == 'f_rate':
        return [{'label': ' '.join(i.split('_')).title(), 'value': i} for i in ['passed', 'failed_1', 'failed_2', 'failed_3', 'failed_all']], []

    elif mode == 'd_specs':
        if start is not None and end is not None:
            return [{'label': i.title(), 'value': i} for i in df.loc[start : end].id.values], []


@app.callback(
    dash.dependencies.Output('graph1', 'figure'),
    [
        dash.dependencies.Input('dataframe', 'children'),
        dash.dependencies.Input('date-range-picker', 'start_date'),
        dash.dependencies.Input('date-range-picker', 'end_date'),
        dash.dependencies.Input('dropdown-select', 'value'),
        dash.dependencies.Input('radio-select', 'value'),
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
        return []


@app.callback(
    [Output('datatable', 'data'),Output('datatable', 'columns'), Output('datatable-div', 'style'), Output('graph-div', 'style')],
    [Input('graph1', 'clickData'),Input('dropdown-select', 'value')],
    [State('dataframe', 'children'),State('radio-select', 'value')]
)
def update_table(clickData, dropdown_select, json_df, radio):
    '''
    '''
    if 'd_specs' in radio:
        if clickData or dropdown_select:
            df = pd.read_json(json_df, orient='split').drop(columns=['created_at'], errors='ignore') 
            
            if dropdown_select:
                # pick the devices selected in the dropdown option
                df = df.loc[[True if str(x) in dropdown_select else False for x in df.id]]
            
            elif clickData:
                df = df.loc[df.id==clickData['points'][0]['text'].split(' ',1)[1]]
            
            return df.to_dict('records'), [{"name": i, "id": i} for i in df.columns if i!='created_at'], dict(display='inline-block'), dict(className='item')
    else:
        return [], [], dict(display='none'), dict(className='1 columns', display='inline-block', width='100%')


# ---------------- MAIN ------------------------ #

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    #debug = os.environ.get('PRODUCTION') is None
    app.run_server(debug=True, host='0.0.0.0', port=port)


'''
Copyright (C) 2019  Otto von Sperling

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <https://www.gnu.org/licenses/>
    
    full license: https://www.gnu.org/licenses/gpl-3.0.en.html
'''