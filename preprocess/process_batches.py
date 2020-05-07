import pandas as pd
data = pd.read_csv("../Current_Data/New_data_updated_names.csv", usecols=['Country','Date','Cases','Deaths','Summary'], 
                  parse_dates=["Date"])

def find_next_batch(count):
    initialCount = count
    found = False
    while not found:
        count += 1
        if data["Date"].loc[count + 1] != data["Date"].loc[count]:
            found = True
            break
    return data.iloc[initialCount:count+1]
