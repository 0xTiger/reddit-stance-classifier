import requests
import csv
import json
import os
from pushlib_utils import get_subs

def backup(data, file):
    with open(file, 'w') as o:
        json.dump(data, o, indent=2)
    print("Saved data @ " + file + ' with size: ' + str(round(os.path.getsize(file) / 1024)) + "KB")

data_file = '..\\assets\\reddit\\polcompass\\polcompass.csv'
save_file = 'user_profiles.json'

with open(data_file) as f:
    reader = csv.reader(f)
    users = {row[2]: row[3] for row in reader}
    total = len(users)

try:
    with open(save_file) as f:
        mldata = json.load(f)
except:
    mldata = {}

i = len(mldata)
for user, stance in users.items():
    if user not in mldata:
        print(user, stance, str(round(i/total*100, 3)) + "% Done")
        mldata[user] = {'stance': stance, 'subs': get_subs(user)}
        i += 1
        if i % 50 == 0: backup(mldata, save_file)
