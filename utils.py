import os
from typing import Iterable, List

import requests
import numpy as np
from requests.auth import HTTPBasicAuth

stancecolormap = {
    'libleft': 'green',
    'libright': 'yellow', 
    'authleft': 'red', 
    'authright': 'blue',
    'left': 'maroon',
    'right': 'cyan',
    'centrist': 'grey',
    'auth': 'purple',
    'lib': 'lime'
}               
stancemap = {
    'libleft': (-1, -1),
    'libright': (-1, 1),
    'authleft': (1, -1),
    'authright': (1, 1),
    'left': (0, -1),
    'right': (0, 1),
    'centrist': (0, 0),
    'auth': (1, 0),
    'lib': (-1, 0)
}
stancemap_inv = {v:k for k,v in stancemap.items()}


def stance_name_from_tuple(t, axis='both'):
    v_pos, h_pos = t
    if axis == 'both': stance = stancemap_inv.get((round(v_pos), round(h_pos)))
    elif axis == 'h': stance = stancemap_inv.get((0, round(h_pos)))
    elif axis == 'v': stance = stancemap_inv.get((round(v_pos), 0))
    elif axis == 'h_binary': stance = stancemap_inv.get((0, np.sign(h_pos)))
    elif axis == 'v_binary': stance = stancemap_inv.get((np.sign(v_pos), 0))
    return stance


class ApiHandler:
    """
    Authorizes via OAuth2 to access the reddit API
    
    For documentation, see:
    https://github.com/reddit-archive/reddit/wiki/API
    https://www.reddit.com/dev/api/
    """
    device_id = None
    app_user_agent = 'tigeer\'s utils module'
    base_url = 'https://oauth.reddit.com'

    def __init__(self, device_id):
        self.device_id = device_id
        self.token_info = self.authorize()

    def authorize(self):
        ACCESS_TOKEN_URL = 'https://www.reddit.com/api/v1/access_token'
        GRANT_TYPE_URL = 'https://oauth.reddit.com/grants/installed_client'
        response = requests.post(
            ACCESS_TOKEN_URL,
            auth=HTTPBasicAuth(
                os.environ['CLIENT_ID'], 
                os.environ['CLIENT_SECRET']
            ),
            data=dict(
                grant_type=GRANT_TYPE_URL,
                device_id=self.device_id
            ),
            headers={'user-agent': self.app_user_agent}
        )
        
        return response.json()
    
    def get(self, endpoint_path, **kwargs):
        access_token = self.token_info['access_token']
        headers = {
            'Authorization': f'bearer {access_token}',
            'user-agent': self.app_user_agent,
            **kwargs.pop('headers', dict())
        }
        response = requests.get(f'{self.base_url}{endpoint_path}', headers=headers, **kwargs)
        return response

    def get_user_data(self, username) -> dict:
        response = self.get(f'/user/{username}/about.json')
        response.raise_for_status()
        data = response.json()
        return data['data']

        
    def get_comment_data(self, username, max_iter=None) -> List[dict]:
        after = '_ignored'
        i = 0
        comments = []
        while (not max_iter or i < max_iter) and after:
            i += 1

            response = self.get(f'/user/{username}/comments.json?limit=100&after={after}')
            response.raise_for_status()
            data = response.json()

            comments_chunk = data['data']['children']
            comments += comments_chunk

            after = data['data']['after']
        return [comment['data'] for comment in comments]


def nested_list_to_table_html(nestediter: Iterable[Iterable]):
    tablestr = '<tbody>'
    for row in nestediter:
        tablestr += '<tr>'
        for i, item in enumerate(row):
            tablestr += f'<td {"id=mainbody" if i != 0 else ""}>{item}</td>'
        tablestr += '</tr>'
    tablestr += '</tbody>'
    return tablestr