import os, re
import pandas as pd
from collections import OrderedDict
import numpy as np
from typing import Any
from datetime import datetime as dt
from datetime import timedelta
import plotly.graph_objs as go

# ---------------------- AUX METHODS FOR PARSER -------------------------- #
def parse_test_results(fname):
    '''
    '''
    min_pattern = ['response bad', 'polarity bad', 'rub+buzz bad', 'thd bad', 'created_at 17.10.2018 13.07.41', 'unit n. f072-00737 bad']
    main_features = ['response', 'polarity', 'rub+buzz', 'thd']
    timestamp = re.compile(r'(\d+\.){2}\d+')
    
    with open('Data/{}'.format(fname), 'r') as f:
        from_file = f.read()

    tmp = [x.strip().lower() for x in from_file.split('\n') if x][1:]
    tmp = ['created_at {}'.format('.'.join(x.split())) if timestamp.match(x) else x for x in tmp]
    
    try:
        if len(tmp) < 6:
            missing_features = list(set([x.split(' ',1)[0] for x in min_pattern]) - set([x.split(' ',1)[0] for x in tmp]))
            print('MISSING:', tmp)            
            
            # if unit is missing and all other 4 features are present
            if (('unit' in missing_features) and (not[x for x in missing_features if x in main_features])):
                if any('bad' in x for x in tmp):
                    overall = 'bad'
                else:
                    overall = 'good'
                tmp.append('unit n. {} {}'.format(fname.split('.',1)[0], overall))
            
            # else if any of the 4 features is missing and overall is 'good'
            elif 'good' == ''.join([re.search('good|bad', x).group(0) for x in tmp if 'unit' in x]):
                tmp = ['{} good'.format(x.split(' ',1)[0]) if x.split(' ',1)[0] in main_features else x for x in main_features+tmp]
                tmp = list(OrderedDict.fromkeys(tmp))
            
                print('FIXED: ',tmp)

            # else if overall is 'bad' and main_features values are missing, infer 'bad' for them
            elif 'bad' == ''.join([re.search('good|bad', x).group(0) for x in tmp if 'unit' in x]):
                tmp = ['{} bad'.format(x.split(' ',1)[0])
                        if x.split(' ',1)[0] in (main_features and missing_features)
                        else x for x in main_features+tmp]

                tmp = list(OrderedDict.fromkeys(tmp))
                tmp = [x for x in tmp if re.search('good|bad', x)!=None]
                print('FIXED:', tmp)

            elif len(tmp)==0:
                tmp = ['{} {}'.format(feature, np.nan) if ('unit' not in feature) else '{} n. {} {}'.format(feature, fname, np.nan) for feature in missing_features]
                print('FIXED:', tmp)

            else:
                raise ValueError('Input file {} has missing values that can\'t be handled yet'.format(fname))
    
    except Exception as e:
        print('ERROR:', e)
        print(tmp, len(tmp))

    return tmp

def extend_test_results(list_of_strings): 
    '''
    '''
    tmpd = {}
    # defines valid columns
    columns = ['response', 'polarity', 'rub+buzz', 'thd', 'created_at', 'id', 'overall']

    # compiles regular expression patters
    result = re.compile('good|bad') 
    model_no = re.compile(r'\w\d{3}-\d{5}')

    for entry in list_of_strings:
        if entry:
            key, value = entry.split(' ',1)
        
            if key in columns:
                tmpd[key] = ''.join(value.split())

            # parses the date/timestamp entry (subs any non-digit character with '.')
            elif re.match('created_at', key): 
                tmpd['created_at'] = re.sub(r'\D', '.', entry)

            # parse the device id and overall result
            elif 'unit' in key: 
                tmpd['overall'] = result.search(''.join(value.split())).group(0) if result.search(value)!=None else 'nan'
                tmpd['id'] = model_no.search(''.join(value.split())).group(0) if model_no.search(value)!=None else 'nan'
    
    return tmpd

def clean_timestamp_series(series):
    '''
    '''
    return series.apply(lambda x: np.nan if ('nan' in str(x)) else re.search(r'(\d+\.){5}\d+', str(x)).group(0))

def pad_timestamp_series(series):
    '''
    '''
    return series.apply(lambda x: np.nan if ('nan' in str(x)) else '.'.join([y.zfill(2) for y in str(x).split('.')]))

def parse_timestamp_series(series):
    '''
    Finds entries in the given Series that do not match the standard format and attempts to fix them
    This method requires that the dataframe where the series comes from be sorted by ['id'].
    '''
    tmp = []

    def find_nearest_neighbor(index, series):
        # finds the nearest neighbor with a valid date                    
        neighbor_index = np.nan
        i = index + 1
        j = index - 1

        while(True):
            if (i < len(series)-1) and (i + (1 if pd.isnull(series[i]) else 0) == i):
                return i
            elif i < len(series)-1:
                i += 1
            
            elif (j - (1 if pd.isnull(series[j]) else 0) == j):
                return j
            elif j > 1:
                j -= 1
            
        return np.nan

    for index, value in series.iteritems():
        NaN_FLAG = pd.isnull(value)

        if not NaN_FLAG:
            try:
                tmp.append(pd.to_datetime(value, format='%d.%m.%Y.%H.%M.%S', errors='raise'))
            
            except ValueError as e:
                print('TIMESTAMP_PARSE_WARNING:', e)
                print('... attempting to fix the format:')
        
                date_pattern = re.compile(r'(\d+\.){5}\d+')
                date_to_fix = date_pattern.search(str(e)).group(0)
                
                # grabs the alleged day and month
                first, second, tail = date_to_fix.split('.',2) 
                
                if ((int(first) <= 12) and (int(second) > 12)):
                    try:
                        tmp.append(pd.to_datetime('{}.{}.{}'.format(second, first, tail), format='%d.%m.%Y.%H.%M.%S'))
                    
                    except Exception as ex:
                        print('\tFAILED to handle timestamp format exception: ', ex)
                    
                    else:
                        print('\tSUCCEEDED in handling exception for timestamp format.')
                        pass
        
                elif ((int(first) > 12) and (int(second) > 12)):

                    try:
                        # find the nearest neighbor with a valid date            
                        neighbor_index = find_nearest_neighbor(index, series)
                        
                        if pd.isnull(neighbor_index):
                            raise IndexError('Could not find neighbor with valid timestamp')
                    
                    except IndexError as ex:
                        print(e, series[index])
                        pass
                    
                    else:
                        new_date = '{}.{}'.format(str(series[neighbor_index]).rsplit('.',3)[0], value.split('.', 3)[-1])
                
                    try: # to approxiamte the date from a neighbor, the original dataframe must be sorted by ['id'], though.
                        tmp.append(pd.to_datetime(new_date, format='%d.%m.%Y.%H.%M.%S'))
                    
                    except Exception as ex:
                        print('\tFAILED to handle timestamp format exception: ', ex)
                    
                    else:
                        print('\tSUCCEEDED in handling exception for timestamp format.')
                        pass
        
        else:
            print('TIMESTAMP_PARSE_WARNING: time data \'{}\' does not match format \'%d.%m.%Y.%H.%M.%S\' (index: {})'.format(value, index))
            print('... attempting to fix the format:')

            # find the next neighbor with a valid timestamp to approximate
            try:
                neighbor_index = find_nearest_neighbor(index, series)
                
                if pd.isnull(neighbor_index):
                    raise IndexError('Could not find neighbor with valid timestamp')
            
            except IndexError as ex:
                print(e, series[index])
                pass
            
            else:
                new_date = str(series[neighbor_index])
        
            try: # to approxiamte the date from a neighbor, the original dataframe must be sorted by ['id'], though.
                tmp.append(pd.to_datetime(new_date, format='%d.%m.%Y.%H.%M.%S'))
            
            except Exception as ex:
                print('\tFAILED to handle timestamp format exception: ', ex)
            
            else:
                print('\tSUCCEEDED in handling exception for timestamp format.')
                pass

    return tmp

def parse_benchmark_state(df):
    '''
    Parses the number of failed tests for each Orion device in the dataframe
    Returns a list of states that can be used to create a new column in the dataframe
    '''
    list_of_states = []
    for index, value in df.iterrows():
        try:
            if 'good' in str(value.overall):
                list_of_states.append('passed')
        
            elif 'bad' in str(value.overall):
                list_of_states.append('failed_{}'.format((value.value_counts().bad - 1)))

            elif 'nan' in str(value.overall):
                list_of_states.append('nan')

        except Exception as e:
            print('BENCHMARK_STATE_PARSER_ERROR:', value)
            print(pd.isnull(value).value_counts())

    return list_of_states

def load_testresults_todataframe(path, is_csv=False):
    '''
    FUTURE feature:
        handle single files (txt, csv and json)
    '''
    # parses the text files into a list of dictionaries that will be used to create the dataframe
    list_of_dicts = []
    for txt_file in os.listdir(path):
        from_file = parse_test_results(txt_file)

        list_of_dicts.append(extend_test_results(from_file))
    
    # creates the dataframe
    df = pd.DataFrame(list_of_dicts)

    # sort by ['id'] to enable extra error handling in parse_timestamp_series()
    df.sort_values(by=['id'], inplace=True, ascending=False, kind='mergesort')
    df.reset_index(inplace=True, drop=True)

    # standardizes the timestamp format in 'created_at' and transforms to datetime
    df.created_at = clean_timestamp_series(df.created_at)
    df.created_at = pad_timestamp_series(df.created_at)
    df.created_at = parse_timestamp_series(df.created_at)

    # finds and drop rows that have no valid field
    df.replace(to_replace='nan', value=np.nan, inplace=True)
    df.dropna(how='all', inplace=True)
    
    # extends the dataframe to have columns states (the number of failed tests if any, or passed if none)
    df['state'] = parse_benchmark_state(df)

    return df


# ---------------------- AUX METHODS FOR DASHBOARD -------------------------- #

# testing out typing (https://docs.python.org/3/library/typing.html)
def update_windroseplot(in_df: pd.DataFrame, start: dt.date, end: dt.date, in_focus: Any) -> dict:
    '''
    '''
    colors = dict(passed='#009f00', failed_1='#ebaca2', failed_2='#e0907a', failed_3='#ce6a6b', failed_all='#ba4c49', nan='#4a919e')

    end = end + timedelta(days=1)

    if not in_focus:
        df = in_df.copy()
        df = df.loc[start : end]    

    else:
        df = in_df[(in_df.id.isin(in_focus))].copy()
        df = df.loc[start : end]

        

    return {
        'data': [
            go.Scatterpolar(
                r = [x*2 for x in range(5, len(df.loc[df.state==state])+5)],
                theta = [360*x for x in np.random.rand(len(df.loc[df.state==state]))],
                text=['Id: {}'.format(str(x)) for x in df.loc[df.state==state, 'id'].values],
                hoverinfo = 'text',
                name=state,
                mode = 'markers',
                marker = dict(
                    color = colors[state],
                    size = 20,
                    opacity=0.75,
                    line = dict(
                        color = "black"
                    ),
                ),
            ) for state in df.state.unique()
        ],
        'layout': go.Layout(
            title='Orion Devices',
            font=dict(size=18),
            hoverlabel=dict(namelength=20),
            showlegend=True,
            legend=dict(font=dict(size=16)),
            autosize=True,
            #width=1700,
            #height=800,
            polar = dict(
                domain = dict(
                    x = [0, 1],
                    y = [0, 1]
                ),
                bgcolor = 'rgba(74, 145, 158, 0)',
                angularaxis = dict(
                    tickwidth = 0,
                    linewidth = 3,
                    layer = "below traces",
                    #tickvals=,
                    #ticktext=,
                    #nticks= len(np.unique(df[start : end].index.date)),
                    showticklabels=False,
                    showgrid=False,
                    showline=False,
                    direction = 'clockwise',
                    rotation=180,

                ),
                radialaxis = dict(
                    autorange=True,
                    showline = False,
                    linewidth = 0,
                    tickwidth = 0,
                    gridwidth = 2,
                    showgrid=True,
                    showticklabels=False,
                ),
                    sector = [0, 360],
            ),
            paper_bgcolor = 'rgba(0,0,0,0)',
        )
    }

def update_barplot(in_df: pd.DataFrame, start: dt.date, end: dt.date, in_focus: Any) -> dict:
    '''
    '''
    colors = dict(passed='#bed3c3', failed_1='#ebaca2', failed_2='#e0907a', failed_3='#ce6a6b', failed_all='#ba4c49', nan='#4a919e')

    end = end + timedelta(days=1)
    
    if not in_focus:
        df = in_df.copy()
        df = df.loc[start : end]    

    else:
        df = in_df[(in_df.state.isin(in_focus))].copy()
        df = df.loc[start : end]

    # for each state in 'in_focus', we plot 'td' days around the pole
    overall_s = df.state.unique()
    overall_series = {}
    
    for feat in overall_s:
        overall_series[feat] = df[(df.state==feat)].state.resample('D').count().replace(0, np.nan).dropna()
    
    # for each day, calculate the failure rate
    if not in_focus or (any(['failed' in x for x in in_focus]) and any(['passed' in x for x in in_focus])):
        fail_rate = {}
        for date in np.unique(df.index.date):
            d = date.strftime('%Y-%m-%d')
            fail_n = sum([y for (x,y) in zip(df[d].state.value_counts().index, df[d].state.value_counts().values) if 'fail' in x])

            if df[d].state.value_counts()['passed'] > 0:
                fail_rate[date.strftime('%b %d')] = (fail_n  / (df[d].state.value_counts()['passed'] + fail_n))*100
            
            else:
                fail_rate[date] = 1

        # calculate the standard deviation for the series
        std = np.std(list(fail_rate.values()))

    # define data properties for our chart
    my_data = [
        go.Bar(
                #x = overall_series[state].index,
                x = [x.strftime('%b %d') for x in np.unique(overall_series[state].index.date)],
                y = overall_series[state].values,
                text = [str(x) for x in overall_series[state].values],
                hoverinfo = 'text',
                textposition = 'auto',
                opacity=1,
                marker=dict(color=colors[state]),
                name=state,
                
            ) for state in overall_series.keys()
    ]
    if not in_focus or (any(['failed' in x for x in in_focus]) and any(['passed' in x for x in in_focus])):
        my_data.extend([
            go.Scatter(
                mode='lines',
                x = [x for x in fail_rate.keys()],
                y = list(fail_rate.values()),
                name='Fail Rate ± Standard Deviation',
                hoverinfo = 'text',
                text=[(re.search(r'(?<=\.)(\d){2}', str(x)).group(0)+'% ± '+str(y)) for (x, y) in zip(list(fail_rate.values()), [std]*len(list(fail_rate.values())))],
                yaxis='y2',
                error_y=dict(
                    type='percent',
                    value=std,
                    #type='data',
                    #array=[std]*len(list(fail_rate.values())),
                    visible=True
                ),
                marker=dict(color='#c97b42')

            ),

        ])

    # define layout properties for our chart
    layout = go.Layout(
        title= ('Overview'),
        titlefont=dict(
            family='Courier New, monospace',
            size=15,
            color='#7f7f7f'
        ),
        autosize=False,
        height=800,
        width=800,
        hoverlabel=dict(namelength=35),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        #barmode='group',
        margin={'l': 30, 'r': 30},
        hovermode='closest',
        bargap=0.025,
        bargroupgap=0.005,
        legend=dict(
            x=0,
            y=1.0,
            bgcolor='rgba(255, 255, 255, 0)',
            bordercolor='rgba(255, 255, 255, 0)'
        ),

        yaxis=dict(
            tickfont=dict(
                color='#7f7f7f'
            ),
            domain=[0, .7],
            type='log',
            autorange=True,
            showgrid=False,
            showline=False,
            showticklabels=False,
        ),
        yaxis2=dict(
            side='right',
            #overlaying='y',
            domain=[.7,.9],
            titlefont=dict(
                color='#7f7f7f'
            ),
            tickfont=dict(
                color='#7f7f7f'
            ),
            autorange=True,
            #range=[0,1],
            showgrid=False,
            showline=False,
            showticklabels=False,
            zeroline=False,
        )
    )

    return go.Figure(data=my_data, layout=layout)


# debugging purposes -------------------------------------------------------------------
if __name__ == '__main__':
    df = load_testresults_todataframe('Data/')
    update_barplot(df, dt(2018,9,4), dt(2018,10,17), ['passed', 'failed_2'])

'''
SAVING INTERESTING PATTERNS

[1] - dict of (feature: series) where the series is a resampled count of the occurance of the feature per day (only ones with occurances)
It could be useful in a pie chart:

features = df.state.np.unique()
    feature_series = {}
    
    for feat in features:
        feature_series[feat] = df[(df.state==feat)].state.resample('D').count().replace(0, np.nan).dropna()

[2] - data field for a graph figure

'data': [
            go.SOMEPLOT(
                r = feature_series[feature].values,
                theta = [x.strftime('%d %b') for x in feature_series[feature].index],
                text= [feature]*len(td),
                name=feature,
                mode = 'markers',
                marker = dict(
                    color = color,
                    size = 15,
                    line = dict(
                        color = "white"
                    ),
                    opacity=0.7,
                ),
            ) for (feature, color) in zip(features, colors)
        ],
'''
