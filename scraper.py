import csv
from requests.exceptions import HTTPError
from utils import get_comment_data, get_user_data
from tables import User, Comment, Stance
from connections import db

data_file = '../polcompass/data/polcompass.csv'
save_file = 'user_profiles.zip'
nonexist_file = 'nonexist.csv'

with open(nonexist_file) as f:
    reader = csv.reader(f)
    nonexist = {row[0] for row in reader}

already_scraped = {u[0] for u in User.query.with_entities(User.name)}
with open(data_file) as f:
    reader = csv.reader(f)
    usernames = {row[2]: row[3] for row in reader if row[2] not in nonexist and row[2] not in already_scraped}
    total = len(usernames)

nonexist_new = set() # Buffer-Like construction that we use to write non-existent users to csv
for i, (username, stance_name) in enumerate(usernames.items()):
    if stance_name == 'libright2':
        stance_name = 'libright'
    if stance_name == 'CENTG':
        stance_name = 'centrist'
    if stance_name != 'None' and not User.from_name(username):
        try:
            user_data = get_user_data(username)
            comments_data = get_comment_data(username)
        except HTTPError as e:
            print(f'{username:<24} | HTTPError {e.response.status_code} thrown')
            if e.response.status_code in [404, 403]:
                nonexist_new.add(username)
            continue

        user = User(**user_data)
        user.comments = [Comment(**comment_data) for comment_data in comments_data]
        user.stance = Stance.from_str(username, stance_name)
        db.session.add(user)
        db.session.commit()

        print(f'{username:<24} | {len(comments_data)} comments gathered')
        if i % 20 == 0: 
            tablesize = db.engine.execute("SELECT pg_size_pretty(pg_total_relation_size('public.comment'))").first()[0]
            print(f'Table size in db: {tablesize}')

            with open(nonexist_file, 'a') as f:
                writer = csv.writer(f)
                writer.writerows([[name] for name in nonexist_new])
                nonexist_new = set()
