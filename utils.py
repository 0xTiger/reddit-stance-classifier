import numpy as np
import json
import requests


def stance_name_from_tuple(t, axis='both'):
    v_pos, h_pos = t
    if axis == 'both': stance = stancemap_inv.get((round(v_pos), round(h_pos)))
    if axis == 'h': stance = stancemap_inv.get((0, round(h_pos)))
    if axis == 'v': stance = stancemap_inv.get((round(v_pos), 0))
    if axis == 'h_binary': stance = stancemap_inv.get((0, np.sign(h_pos)))
    if axis == 'v_binary': stance = stancemap_inv.get((np.sign(v_pos), 0))
    return stance


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