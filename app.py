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

app = dash.Dash()
app.css.append_css({
    "external_url": "https://codepen.io/chriddyp/pen/bWLwgP.css"
})

##############################################################
#                                                            #
#                 A U X - M E T H O D S                      #
#                                                            #
#############################################################

def load_test_results(file_name):
    '''
    '''
    with open('Data/{}'.format(file_name), 'r') as f:
        from_file = f.read()
     
        return [x.strip().lower() for x in from_file.split('\n') if x][1:]

def parse_test_results(list_of_strings): 
    '''
    '''
    tmpd = {}
    # defines valid columns
    columns = ['response', 'polarity', 'rub+buzz', 'thd', 'created_at', 'id', 'overall']

    # compiles regular expression patters
    result = re.compile('good|bad') 
    model_no = re.compile(r'\w\d{3}-\d{5}')

    for entry in list_of_strings:
        key, value = entry.split(' ',1)
    
        if key in columns:
            tmpd[key] = ''.join(value.split())
    
        # parses the date/timestamp entry (subs any non-digit character with '.')
        elif re.match('\d+', key): 
            tmpd['created_at'] = re.sub(r'\D', '.', entry)
    
        # parse the device id and overall result
        elif 'unit' in key: 
            tmpd['overall'] = result.search(''.join(value.split())).group(0)
            tmpd['id'] = model_no.search(''.join(value.split())).group(0)
    
    return tmpd

def clean_timestamp_series(series):
    '''
    '''
    return series.apply(lambda x: re.search(r'\d+.\d+.\d+.\d+.\d+.\d+', str(x)).group(0) if not pd.isnull(x) else x)

def pad_timestamp_series(series):
    '''
    '''
    return series.apply(lambda x: '.'.join([y.zfill(2) for y in str(x).split('.')]))

def parse_timestamp_series(series):
    '''
    Finds entries in the given Series that do not match the standard format and attempts to fix them
    This method requires that the dataframe where the series comes from be sorted by ['id'].
    '''
    tmp = []
    for index, value in series.iteritems():
        try:
            tmp.append(pd.to_datetime(value, format='%d.%m.%Y.%H.%M.%S'))
        
        except ValueError as e:
            print('TIMESTAMP_PARSE_ERROR:', e)
            if 'does not match format' in str(e):
                print('... attempting to fix the format:')
                date_pattern = re.compile(r'\d+.\d+.\d+.\d+.\d+.\d+')
                date_to_fix = date_pattern.search(str(e)).group(0)
                
                # grabs the alleged day and month
                first, second, tail = date_to_fix.split('.',2) 
                
                if (int(first) <= 12 and int(second) > 12):
                    try:
                        tmp.append(pd.to_datetime('{}.{}.{}'.format(second, first, tail), format='%d.%m.%Y.%H.%M.%S'))
                    
                    except Exception as ex:
                        print('\tFAILED to handle timestamp format exception: ', ex)
                    
                    else:
                        print('\tSUCCEEDED in handling exception for timestamp format.')
                        pass
                
                else:
                    date_from_neighbor = series.iloc[index+1]
                    new_date = '{}.{}'.format(date_from_neighbor.rsplit('.',3)[0], value.split('.',3)[-1])
                    
                    try: # to approxiamte the date from a neighbor, the original dataframe must be sorted by ['id'], though.
                        tmp.append(pd.to_datetime(new_date, format='%d.%m.%Y.%H.%M.%S'))
                    
                    except Exception as ex:
                        print('\tFAILED to handle timestamp format exception: ', ex)
                    
                    else:
                        print('\tSUCCEEDED in handling exception for timestamp format.')
                        pass
    return tmp

def load_testresults_todataframe(path):
    '''
    '''
    # parses the text files into a list of dictionaries that will be used to create the dataframe
    list_of_dicts = []
    for txt_file in os.listdir(path):
        from_file = load_test_results(txt_file)

        list_of_dicts.append(parse_test_results(from_file))
    
    # creates the dataframe
    df = pd.DataFrame(list_of_dicts)

    # sort by ['id'] to enable extra error handling in parse_timestamp_series()
    df.sort_values(by=['id'], inplace=True, ascending=False, kind='mergesort'))
    df.reset_index(inplace=True, drop=True)

    # standardizes the timestamp format in 'created_at' and transforms to datetime
    df.created_at = clean_timestamp_series(df.created_at)
    df.created_at = pad_timestamp_series(df.created_at)
    df.created_at = parse_timestamp_series(df.created_at)



# Picked with http://tristen.ca/hcl-picker/#/hlc/6/1.05/251C2A/E98F55
COLORS = ['#608F40', '#727D29', '#7C691D', '#80561E', '#7D4525']
STATES = ['passed', 'failed_1', 'failed_2', 'failed_3', 'failed_all']


##############################################################
#                                                            #
#                   L  A  Y  O  U  T                         #
#                                                            #
##############################################################


app.layout = html.Div(children=[
    html.H2(children='Orion Dashboard', style={
        'textAlign': 'center',
    }),
    # Date Picker
    html.Div([
        dcc.DatePickerRange(
            id='date-range-picker',
            min_date_allowed = orion_df['created_at'].min().to_pydatetime(),
            max_date_allowed = orion_df['created_at'].max().to_pydatetime(),
            initial_visible_month = dt(orion_df['created_at'].max().to_pydatetime().year,
                                       orion_df['created_at'].max().to_pydatetime().month, 1),
            start_date = orion_df['created_at'].min().to_pydatetime(),
            end_date = orion_df['created_at'].max().to_pydatetime(),
    )], className="row ", style={'marginTop': 30, 'marginBottom': 15}),

    # html.Div(id='output-container-date-picker-range-paid-search')
    # ], className="row ", style={'marginTop': 30, 'marginBottom': 15}),

    dcc.Dropdown(
        id='categories',
        options=[{'label': i, 'value': i} for i in orion_df['broader_category'].unique()],
        multi=True
    ),
    dcc.Graph(
        id='speakers-in-daterange',
    ),
    dcc.Graph(
        id='stats-in-daterange',
    )
])


##############################################################
#                                                            #
#            I  N  T  E  R  A  C  T  I  O  N  S              #
#                                                            #
##############################################################


@app.callback(
    dash.dependencies.Output('speakers-in-daterange', 'figure'),
    [
        dash.dependencies.Input('categories', 'value'),
        dash.dependencies.Input('date-range-picker', 'start_date'),
        dash.dependencies.Input('date-range-picker', 'end_date'),
    ])

def update_scatterplot(categories, start_date, end_date):
    if categories is None or categories == []:
        categories = CATEGORIES

    start_date = dt.strptime(start_date, '%Y-%m-%d %H:%M:%S')
    end_date = dt.strptime(end_date, '%Y-%m-%d %H:%M:%S')

    sub_df = orion_df_sub[(orion_df_sub['broader_category'].isin(categories))]
    sub_df = sub_df.loc[[start_date <= x <= end_date for x in sub_df['created_at']]]

    return {
        'data': [
            go.Scatter(
                x=sub_df[(orion_df_sub.state == state)]['created_at'],
                y=sub_df[(orion_df_sub.state == state)]['usd_pledged'],
                text=sub_df[(orion_df_sub.state == state)]['name'],
                mode='markers',
                opacity=0.7,
                marker={
                    'size': 15,
                    'color': color,
                    'line': {'width': 0.5, 'color': 'white'}
                },
                name=state,
            ) for (state, color) in zip(STATES, COLORS)
        ],
        'layout': go.Layout(
            xaxis={'title': 'Date'},
            yaxis={'title': 'USD pledged', 'type': 'log'},
            margin={'l': 40, 'b': 40, 't': 10, 'r': 10},
            legend={'x': 0, 'y': 1},
            hovermode='closest'
        )
    }


@app.callback(
    dash.dependencies.Output('stats-in-daterange', 'figure'),
    [
        dash.dependencies.Input('categories', 'value'),
        dash.dependencies.Input('speakers-in-daterange', 'relayoutData')
    ])
def update_bar_chart(categories, relayoutData):
    if categories is None or categories == []:
        categories = CATEGORIES

    if (relayoutData is not None
            and (not (relayoutData.get('xaxis.autorange') or relayoutData.get('yaxis.autorange')))):
        x0 = dateutil.parser.parse(relayoutData['xaxis.range[0]'])
        x1 = dateutil.parser.parse(relayoutData['xaxis.range[1]'])
        y0 = 10 ** relayoutData['yaxis.range[0]']
        y1 = 10 ** relayoutData['yaxis.range[1]']

        sub_df = orion_df[orion_df.created_at.between(x0, x1) & orion_df.usd_pledged.between(y0, y1)]
    else:
        sub_df = orion_df

    stacked_barchart_df = (
        sub_df[sub_df['broader_category'].isin(categories)]['state'].groupby(sub_df['broader_category'])
        .value_counts(normalize=False)
        .rename('count')
        .to_frame()
        .reset_index('state')
        .pivot(columns='state')
        .reset_index()
    )
    return {
        'data': [
            go.Bar(
                x=stacked_barchart_df['broader_category'],
                y=stacked_barchart_df['count'][state],
                name=state,
                marker={
                    'color': color
                }
            ) for (state, color) in zip(STATES[::-1], COLORS[::-1])
        ],
        'layout': go.Layout(
            yaxis={'title': 'Number of projects'},
            barmode='stack',
            hovermode='closest'
        )
    }



##############################################################
#                                                            #
#                      M  A  I  N                            #
#                                                            #
##############################################################


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('PRODUCTION') is None
    app.run_server(debug=debug, host='0.0.0.0', port=port)
