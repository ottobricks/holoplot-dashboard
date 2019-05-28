import os, re
import pandas as pd
from collections import OrderedDict
from numpy import NaN

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
                tmp = ['{} bad*'.format(x.split(' ',1)[0])
                        if x.split(' ',1)[0] in (main_features and missing_features)
                        else x for x in main_features+tmp]

                tmp = list(OrderedDict.fromkeys(tmp))
                tmp = [x for x in tmp if re.search('good|bad', x)!=None]
                print('FIXED:', tmp)

            elif len(tmp)==0:
                tmp = ['{} {}'.format(feature, NaN) if ('unit' not in feature) else '{} n. {} {}'.format(feature, fname, NaN) for feature in missing_features]
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
                tmpd['overall'] = result.search(''.join(value.split())).group(0) if result.search(value)!=None else NaN
                tmpd['id'] = model_no.search(''.join(value.split())).group(0) if model_no.search(value)!=None else NaN
    
    return tmpd

def clean_timestamp_series(series):
    '''
    '''
    return series.apply(lambda x: NaN if ('nan' in str(x)) else re.search(r'(\d+\.){5}\d+', str(x)).group(0))

def pad_timestamp_series(series):
    '''
    '''
    return series.apply(lambda x: NaN if ('nan' in str(x)) else '.'.join([y.zfill(2) for y in str(x).split('.')]))

def parse_timestamp_series(series):
    '''
    Finds entries in the given Series that do not match the standard format and attempts to fix them
    This method requires that the dataframe where the series comes from be sorted by ['id'].
    '''
    tmp = []

    def find_nearest_neighbor(index, series):
        # find the nearest neighbor with a valid date                    
        neighbor_index = i = j = index
        while(True):
            if (i + (1 if pd.isnull(series[i]) else 0) == i):
                return i
            elif i < len(series)-1:
                i += 1
            
            elif (j - (1 if pd.isnull(series[j]) else 0) == j):
                return j
            elif j > 1:
                j -= 1
            
        return NaN

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
            # find the next neighbor with a valid timestamp to approximate
            try:
                neighbor_index = find_nearest_neighbor(index, series)
                
                if pd.isnull(neighbor_index):
                    raise IndexError('Could not find neighbor with valid timestamp')
            
            except IndexError as ex:
                print(e, series[index])
                pass
            
            except Exception as ex:
                print('NaN_ERROR', ex, index)
            
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
        
            else:
                list_of_states.append('failed_{}'.format(value.value_counts().bad - 1))

        except Exception as e:
            print('BENCHMARK_STATE_PARSER_ERROR:', value)
            print(pd.isnull(value).value_counts())

    return list_of_states

def load_testresults_todataframe(path):
    '''
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
    df.dropna(how='all', inplace=True)
    df['state'] = parse_benchmark_state(df)

    return df

