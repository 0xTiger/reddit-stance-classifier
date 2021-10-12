import csv
import pandas as pd
from requests.exceptions import HTTPError
from pushlib_utils import get_comment_data, relevant_fields

data_file = '../polcompass/data/polcompass.csv'
save_file = 'user_profiles.zip'

with open(data_file) as f:
    reader = csv.reader(f)
    users = {row[2] for row in reader}
    total = len(users)

try:
    mldata = pd.read_pickle(save_file)
except FileNotFoundError:
    mldata = pd.DataFrame()

for i, user in enumerate(users):
    if mldata.empty or user not in mldata.index.levels[0]:
        try:
            comments = get_comment_data(user)
        except HTTPError as e:
            print(f'{user:<24} | HTTPError {e.response.status_code} thrown')
            continue
        if not comments:
            print(f'{user:<24} | Had no comments')
            continue

        df = pd.DataFrame(comments)[relevant_fields]
        df = pd.concat({user: df}, names=['user']) #Adds level to create MultiIndex
        mldata = pd.concat([mldata, df])
        print(f'{user:<24} | {len(df)} comments gathered')
        if i % 50 == 0: 
            mldata.to_pickle(save_file)
            print(f'Size in memory: {mldata.memory_usage().sum() / 1024 / 1024:.2f}MB')
