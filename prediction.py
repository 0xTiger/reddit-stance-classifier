import pandas as pd
import joblib
from requests.exceptions import HTTPError
from pushlib_utils import get_subs, get_subs_redapi
from custom_transformers import DictFilterer, ToSparseDF, exclude_u_sub

voting_clf = joblib.load('models/clf_ensemble.pkl')
full_pipeline = joblib.load('models/pipeline_ensemble.pkl')
voting_clf2 = joblib.load('models/clf_ensemble2.pkl')
full_pipeline2 = joblib.load('models/pipeline_ensemble2.pkl')

def pred_lean(name):
    try:
        dict = get_subs(name)
    except:
        try:
            dict = get_subs_redapi(name)
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

    series = full_pipeline.transform([dict])
    h_stance = voting_clf.predict(series)[0]
    h_conf = max(voting_clf.predict_proba(series)[0])

    series2 = full_pipeline2.transform([dict])
    v_stance = voting_clf2.predict(series2)[0]
    v_conf = max(voting_clf2.predict_proba(series2)[0])

    return (h_stance, v_stance, h_conf, v_conf)
