import csv
from requests.exceptions import HTTPError
from pushlib_utils import get_comment_data, get_user_data
from tables import User, Comment, Stance
from connections import db

data_file = '../polcompass/data/polcompass.csv'
save_file = 'user_profiles.zip'

with open(data_file) as f:
    reader = csv.reader(f)
    usernames = {row[2]: row[3] for row in reader}
    total = len(usernames)

for i, (username, stance_name) in enumerate(usernames.items()):
    if stance_name == 'libright2':
        stance_name = 'libright'
    if stance_name != 'None' and not User.from_name(username):
        try:
            user_data = get_user_data(username)
            comments_data = get_comment_data(username)
        except HTTPError as e:
            print(f'{username:<24} | HTTPError {e.response.status_code} thrown')
            continue

        user = User(**user_data)
        user.comments = [Comment(**comment_data) for comment_data in comments_data]
        user.stance = Stance.from_str(username, stance_name)
        db.session.add(user)
        db.session.commit()

        print(f'{username:<24} | {len(comments_data)} comments gathered')
        if i % 50 == 0: 
            tablesize = db.engine.execute("SELECT pg_size_pretty(pg_total_relation_size('public.comment'))").result()[0]
            print(f'{tablesize = }')