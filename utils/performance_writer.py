import pandas as pd
 
def save_performance(results, path):
    df = pd.DataFrame(results)
    df.to_csv(path, index=False) 