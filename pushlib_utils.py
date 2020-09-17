import json
import requests

def get_subs(author):
    url = 'https://api.pushshift.io/reddit/search/comment/?author='+str(author)+'&score=%3E0&aggs=subreddit&size=0'
    r = requests.get(url)
    data = json.loads(r.text)
    return {i['key']: i['doc_count'] for i in data['aggs']['subreddit']}
