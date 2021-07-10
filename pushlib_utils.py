import json
import requests
from collections import Counter

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
