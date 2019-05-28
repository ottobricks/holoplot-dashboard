# -*- coding: utf-8 -*-

import os, re
import dash
import dash_core_components as dcc
import dash_html_components as html
import dateutil
import plotly.graph_objs as go
import pandas as pd
from datetime import datetime as dt
from datetime import date, timedelta
import aux_methods as aux

app = dash.Dash()
app.css.append_css({
    "external_url": "https://codepen.io/chriddyp/pen/bWLwgP.css"
})


# ---------------- LOAD THE DATAFRAME ------------------------ #

orion_df = aux.load_testresults_todataframe('Data/')



# ---------------- DASHBOARD LAYOUT ------------------------ #

# Picked with http://tristen.ca/hcl-picker/#/hlc/6/1.05/251C2A/E98F55
COLORS = ['#608F40', '#727D29', '#7C691D', '#80561E', '#7D4525']


app.layout = html.Div(children=[
    html.H2(children='Orion Dashboard', style={
        'textAlign': 'center',
    }),
    # Date Picker
    html.Div([
        dcc.DatePickerRange(
            id='date-range-picker',
            min_date_allowed = orion_df['created_at'].min().to_pydatetime().date(),
            max_date_allowed = orion_df['created_at'].max().to_pydatetime().date(),
            initial_visible_month = dt(orion_df['created_at'].max().to_pydatetime().date().year,
                                       orion_df['created_at'].max().to_pydatetime().date().month, 1),
            start_date = orion_df['created_at'].max().to_pydatetime().date() - timedelta(days=5),
            end_date = orion_df['created_at'].max().to_pydatetime().date(),
            display_format='D MMM, YYYY',
    )], className="row", style={'marginTop': 30, 'marginBottom': 15}),
    
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
        #options=[{'label': i, 'value': i} for i in STATES],
        multi=True
    ),
    dcc.Graph(
        id='speakers-in-daterange',
    ),
    dcc.Graph(
        id='stats-in-daterange',
    )
])


# ---------------- DASHBOARD INTERACTIONS ------------------------ #

@app.callback(
    dash.dependencies.Output('dropdown_states', 'options'),
    [
        dash.dependencies.Input('radio_states', 'value'),
        dash.dependencies.Input('date-range-picker', 'start_date'),
        dash.dependencies.Input('date-range-picker', 'end_date')
    ]
)
def update_dropdown_states(mode, start, end):
    '''
    '''
    if mode == 'f_rate':
        return [{'label': ' '.join(i.split('_')).title(), 'value': i} for i in ['passed', 'failed_1', 'failed_2', 'failed_3', 'failed_all']]
    
    elif mode == 't_points':
        return [{'label': i.title(), 'value': i} for i in ['response', 'polarity', 'rub+buzz', 'thd']]

    elif mode == 'd_specs':
        if start is not None and end is not None:
            return [{'label': i.title(), 'value': i} for i in orion_df.id.loc[orion_df.created_at.between(dt.strptime(start, '%Y-%m-%d'), dt.strptime(end, '%Y-%m-%d'))]]

# @app.callback(
#     dash.dependencies.Output('speakers-in-daterange', 'figure'),
#     [
#         dash.dependencies.Input('date-range-picker', 'start_date'),
#         dash.dependencies.Input('date-range-picker', 'end_date'),
#         dash.dependencies.Input('dropdown_states', 'value')
#     ]
# )
# def update_scatterplot(start_date, end_date, states):
#     start_date = dt.strptime(start_date, '%Y-%m-%d')
#     end_date = dt.strptime(end_date, '%Y-%m-%d')

#     sub_df = orion_df[(orion_df.state.isin(states))]
#     sub_df = sub_df.loc[[start_date <= x <= end_date for x in sub_df.created_at.date()]]

#     return {
#         'data': [
#             go.Scatter(
#                 x = sub_df[(orion_df_sub.state == state)].created_at.date(),
#                 y = sub_df[(orion_df_sub.state == state)].created_at.time(),
#                 text = sub_df[(orion_df_sub.state == state)].id,
                
#                 mode='markers',
#                 opacity=0.7,
#                 marker={
#                     'size': 15,
#                     'color': color,
#                     'line': {'width': 0.5, 'color': 'white'}
#                 },
#                 name=state,
#             ) for (state, color) in zip(states, COLORS)
#         ],
#         'layout': go.Layout(
#             xaxis={'title': 'Date'},
#             yaxis={'title': 'Time'},
#             margin={'l': 40, 'b': 40, 't': 10, 'r': 10},
#             legend={'x': 0, 'y': 1},
#             hovermode='closest'
#         )
#     }


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
