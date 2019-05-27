import os, re, logging
import pandas as pd

logging.basicConfig(filename='output.log', filemode='w',level=logging.WARNING)

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
            timestamp = pd.to_datetime(value, format='%d.%m.%Y.%H.%M.%S')
            if not pd.isnull(timestamp):
                tmp.append(timestamp)

            else:
                raise ValueError('Timestamp NaT does not match format.')
        
        except ValueError as e:
            logging.warning('TIMESTAMP_PARSE_WARNING:', e)
            if 'does not match format' in str(e):
                NaT_FLAG = 'NaT' in str(e)
                logging.info('... attempting to fix the format:')
        
                if not NaT_FLAG:
                    date_pattern = re.compile(r'\d+.\d+.\d+.\d+.\d+.\d+')
                    date_to_fix = date_pattern.search(str(e)).group(0)
                
                    # grabs the alleged day and month
                    first, second, tail = date_to_fix.split('.',2) 
                
                if ((not NaT_FLAG) and (int(first) <= 12) and (int(second) > 12)):
                    try:
                        tmp.append(pd.to_datetime('{}.{}.{}'.format(second, first, tail), format='%d.%m.%Y.%H.%M.%S'))
                    
                    except Exception as ex:
                        logging.error('\tFAILED to handle timestamp format exception: ', ex)
                    
                    else:
                        logging.info('\tSUCCEEDED in handling exception for timestamp format.')
                        pass
                
                else:
                    date_from_neighbor = series.iloc[index+1]
                    if NaT_FLAG:
                        time = date_from_neighbor.split('.', 3)[-1]
                    
                    else:
                        time = value.split('.', 3)[-1]

                    new_date = '{}.{}'.format(date_from_neighbor.rsplit('.',3)[0], time)
                    
                    try: # to approxiamte the date from a neighbor, the original dataframe must be sorted by ['id'], though.
                        tmp.append(pd.to_datetime(new_date, format='%d.%m.%Y.%H.%M.%S'))
                    
                    except Exception as ex:
                        logging.error('\tFAILED to handle timestamp format exception: ', ex)
                    
                    else:
                        logging.info('\tSUCCEEDED in handling exception for timestamp format.')
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
    df.sort_values(by=['id'], inplace=True, ascending=False, kind='mergesort')
    df.reset_index(inplace=True, drop=True)

    # standardizes the timestamp format in 'created_at' and transforms to datetime
    df.created_at = clean_timestamp_series(df.created_at)
    df.created_at = pad_timestamp_series(df.created_at)
    df.created_at = parse_timestamp_series(df.created_at)

    return df

def parse_benchmark_state(df):
    '''
    Parses the number of failed tests for each Orion device in the dataframe
    Returns a list of states that can be used to create a new column in the dataframe
    '''
    list_of_states = []
    for index, value in df.iterrows():
        if 'good' in str(value.overall):
            list_of_states.append('passed')
        
        else:
            list_of_states.append('failed_{}'.format(value.value_counts().bad - 1))
    
    return list_of_states
