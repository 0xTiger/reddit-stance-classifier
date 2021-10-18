import json
import requests


def get_user_data(username):
    url = f'https://www.reddit.com/user/{username}/about.json'
    r = requests.get(url, headers={'user-agent': 'tigeer\'s pushlib_utils module'})
    r.raise_for_status()
    data = json.loads(r.text)
    return data['data']

    
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