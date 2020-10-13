import pandas as pd
import joblib
from pushlib_utils import get_subs
from custom_transformers import DictFilterer, ToSparseDF, exclude_u_sub

voting_clf = joblib.load('models/clf_ensemble.pkl')
full_pipeline = joblib.load('models/pipeline_ensemble.pkl')
voting_clf2 = joblib.load('models/clf_ensemble2.pkl')
full_pipeline2 = joblib.load('models/pipeline_ensemble2.pkl')

def pred_lean(name):
    dict = get_subs(name)
    if not dict:
        raise ValueError(f'User \'{name}\' does not exist')

    series = full_pipeline.transform([dict])
    h_stance = voting_clf.predict(series)[0]
    h_conf = max(voting_clf.predict_proba(series)[0])

    series2 = full_pipeline2.transform([dict])
    v_stance = voting_clf2.predict(series2)[0]
    v_conf = max(voting_clf2.predict_proba(series2)[0])

    return (h_stance, v_stance, h_conf, v_conf)

# full_pipeline_nn = joblib.load('models/pipeline_nn.pkl')
# model = joblib.load('models/clf_nn.pkl')
#
# def pred_lean_nn(names):
#     if type(names) == str: names = [names]
#     dict = [get_subs(name) for name in names]
#     inst = full_pipeline_nn.transform(dict).todense()
#     return model.predict_classes(inst)
