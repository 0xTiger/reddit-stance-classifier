import json
import requests
from collections import Counter

stancecolormap = {'libleft': 'green', 
                'libright': 'yellow', 
                'authleft': 'red', 
                'authright': 'blue',
                'left': 'maroon',
                'right': 'cyan',
                'centrist': 'grey',
                'auth': 'purple',
                'lib': 'lime'}
                
stancemap = {'libleft': (-1, -1), 
        'libright': (-1, 1), 
        'authleft': (1, -1), 
        'authright': (1, 1),
        'left': (0, -1),
        'right': (0, 1),
        'centrist': (0, 0),
        'auth': (1, 0),
        'lib': (-1, 0)}

stancemap_inv = {v:k for k,v in stancemap.items()}

def get_subs(username, max_iter=None):
    after = '_ignored'
    i = 0
    comments_by_sub = Counter()
    while (not max_iter or i < max_iter) and after:
        i += 1

        url = f'https://www.reddit.com/user/{username}/comments.json?limit=100&after={after}'
        r = requests.get(url, headers={'user-agent': 'tigeer\'s pushlib_utils module'})
        r.raise_for_status()
        data = json.loads(r.text)

        comments = data['data']['children']
        comments_by_sub.update(comment['data']['subreddit'] for comment in comments)

        after = data['data']['after']
    return comments_by_sub


def get_comment_data(username, max_iter=None):
    after = '_ignored'
    i = 0
    comments = []
    while (not max_iter or i < max_iter) and after:
        i += 1

        url = f'https://www.reddit.com/user/{username}/comments.json?limit=100&after={after}'
        r = requests.get(url, headers={'user-agent': 'tigeer\'s pushlib_utils module'})
        r.raise_for_status()
        data = json.loads(r.text)

        comments_chunk = data['data']['children']
        comments += comments_chunk

        after = data['data']['after']
    return [comment['data'] for comment in comments]


relevant_fields = ['subreddit',
                    'controversiality',
                    'total_awards_received',
                    'gilded',
                    'author',
                    'num_comments',
                    'created_utc',
                    'parent_id',
                    'link_id',
                    'id',
                    'score',
                    'author_fullname',
                    'over_18',
                    'body',
                    'link_title',
                    'link_author',
                    'is_submitter',
                    'author_flair_text',
                    'created',
                    'locked',
                    'quarantine',
                    'subreddit_type']