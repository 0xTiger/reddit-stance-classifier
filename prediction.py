import joblib
from requests.exceptions import HTTPError
from pushlib_utils import get_subs

full_pipeline = joblib.load('models/ensemble.pkl')

def pred_lean(name):
    try:
        dict = get_subs(name)
        total = sum(n for n in dict.values())
        if total < 800 or total >= 1000 + 10:
            scale = 1
        elif 800 <= total < 950:
            scale = ((1200 - 800)/(950 - 800)*(total - 800) + 800)/total
        elif 950 <= total < 1000 + 10:
            scale = ((3500 - 1200)/(1000 - 950)*(total - 950) + 1200)/total
            
        dict = {k: scale*v for k,v in dict.items()}

    except HTTPError as err:
        if err.response.status_code == 404:
            raise ValueError(f'User \'{name}\' does not exist')
    if not dict:
        raise ValueError(f'User \'{name}\' has no comment history')

    return full_pipeline.predict([dict])[0]
