import json
import requests

def get_subs(username, max_iter=None):
    after = '_ignored'
    i = 0
    comments_by_sub = dict()
    while (not max_iter or i < max_iter) and after:
        i += 1

        url = f'https://www.reddit.com/user/{username}/comments.json?limit=100&after={after}'
        r = requests.get(url, headers={'user-agent': 'tigeer\'s pushlib_utils module'})
        r.raise_for_status()
        data = json.loads(r.text)

        for comment in data['data']['children']:
            sub = comment['data']['subreddit']
            if sub in comments_by_sub:
                comments_by_sub[sub] += 1
            else:
                comments_by_sub[sub] = 1

        after = data['data']['after']
    return comments_by_sub
