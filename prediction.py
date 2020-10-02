import pandas as pd
import joblib
from pushlib_utils import get_subs
from custom_transformers import DictFilterer, exclude_u_sub

voting_clf = joblib.load('models/clf_ensemble.pkl')
full_pipeline = joblib.load('models/pipeline_ensemble.pkl')
non_empty = joblib.load('models/non_empty_ensemble.pkl')
best_feat = joblib.load('models/best_feat_ensemble.pkl')

def pred_lean(name):
    dict = get_subs(name)
    if not dict:
        raise ValueError(f'User \'{name}\' does not exist')
    series = full_pipeline.transform([dict])
    series = pd.DataFrame.sparse.from_spmatrix(series, columns=best_feat, index=[name])
    series = series[non_empty]
    return voting_clf.predict(series)[0]

# full_pipeline_nn = joblib.load('models/pipeline_nn.pkl')
# model = joblib.load('models/clf_nn.pkl')
#
# def pred_lean_nn(names):
#     if type(names) == str: names = [names]
#     dict = [get_subs(name) for name in names]
#     inst = full_pipeline_nn.transform(dict).todense()
#     return model.predict_classes(inst)
