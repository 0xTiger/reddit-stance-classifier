import json
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
def warn(*args, **kwargs):
    pass
import warnings
warnings.warn = warn
from sklearn.feature_extraction import DictVectorizer
from sklearn.feature_selection import VarianceThreshold
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import StratifiedShuffleSplit, cross_val_predict, GridSearchCV
from sklearn.metrics import confusion_matrix, precision_score, recall_score
from sklearn.ensemble import RandomForestClassifier, VotingClassifier
from sklearn.multioutput import MultiOutputClassifier
from custom_transformers import DictFilterer, ToSparseDF, exclude_u_sub
import joblib
import argparse

parser = argparse.ArgumentParser()
parser.add_argument('-p', '--persist', action='store_true', help='Specify whether to make the model persistent in models/*')

args = parser.parse_args()

"""
TODO
find best model:
best sofar: LinearSVC(C=100, loss='hinge', random_state=42)--
best sofar: RandomForestClassifier(min_samples_leaf=3, random_state=42)--
best sofar: VotingClassifier()--

Try different regularization (possibly less this time with larger dataset)
using GridSearchCV, also try giving more noteable users a greater sample_weight in .fit() method for the
"""
with open('user_profiles.json') as f:
    mldata = json.load(f)

conditions = lambda user, data: user != '[deleted]'
gen = ((user, data) for user, data in mldata.items() if conditions(user, data))

# stancemap = {'libleft': (-1, -1), 
#                 'libright': (-1, 1), 
#                 'authleft': (1, -1), 
#                 'authright': (1, 1),
#                 'left': (0, -1),
#                 'right': (0, 1),
#                 'centrist': (0, 0),
#                 'auth': (1, 0),
#                 'lib': (-1, 0)}

stancemap = {'libleft': (0, 0), 
                'libright': (0, 1), 
                'authleft': (1, 0), 
                'authright': (1, 1)}

stancemap_inv = {v:k for k,v in stancemap.items()}

def stances_from_tuple(y, axis='both'):
    if axis == 'both': stances = [stancemap_inv.get(tuple(t)) for t in y]
    if axis == 'h': stances = [stancemap_inv.get((0, t[1])) for t in y]
    if axis == 'v': stances = [stancemap_inv.get((t[0], 0)) for t in y]
    return np.array(stances)

users, features, labels = [], [], []
for user, data in gen:
    label = stancemap.get(data['stance'])
    if label:
        features.append(data['subs'])
        labels.append(label)

labels = np.array(labels)
features = pd.Series(features)

splitter = StratifiedShuffleSplit(n_splits=1, test_size=0.2, random_state=42)
for train_index, test_index in splitter.split(features, labels):
    X_train, y_train = features[train_index], labels[train_index]
    X_test, y_test = features[test_index], labels[test_index]

log_clf = LogisticRegression(C=0.2, penalty='l1', solver='liblinear')
forest_clf = RandomForestClassifier(min_samples_leaf=5, random_state=42)
voting_clf = VotingClassifier(estimators=[('forest', forest_clf), ('logit', log_clf)],
                                voting='soft')

multi_clf = MultiOutputClassifier(forest_clf)

full_pipeline = Pipeline([('filterer', DictFilterer(exclude_u_sub)), #k in rel_subs
                            ('vectorizer', DictVectorizer(sparse=True)),
                            ('selectKBest', VarianceThreshold(threshold=1)),
                            ('scaler', StandardScaler(with_mean=False)),
                            ('framer', ToSparseDF()),
                            ('clf', multi_clf)])

if __name__ == '__main__':
    y_pred = cross_val_predict(full_pipeline, X_train, y_train, cv=5, n_jobs=-1)

    y_train_stances = stances_from_tuple(y_train)
    y_pred_stances = stances_from_tuple(y_pred)

    y_train_h_stances = stances_from_tuple(y_train, axis='h')
    y_pred_h_stances = stances_from_tuple(y_pred, axis='h')
    conf_mx = confusion_matrix(y_train_stances, y_pred_stances)    

    print(y_train_stances)
    print(y_pred_stances)
    print(conf_mx)
    print('Precision: ', precision_score(y_train_stances, y_pred_stances, average='weighted'))
    print('Recall: ', recall_score(y_train_stances, y_pred_stances, average='weighted'))

    conf_mx = confusion_matrix(y_train_h_stances, y_pred_h_stances)
    print(conf_mx)
    print('Precision: ', precision_score(y_train_h_stances, y_pred_h_stances, average='weighted'))
    print('Recall: ', recall_score(y_train_h_stances, y_pred_h_stances, average='weighted'))
    # fig, ax = plt.subplots()
    # cax = ax.matshow(conf_mx, cmap=plt.cm.gray)
    # fig.colorbar(cax)

    # ax.set_xticks(list(range(len(h_stances))))
    # ax.set_yticks(list(range(len(h_stances))))
    # ax.set_xticklabels(h_stances, rotation=45)
    # ax.set_yticklabels(h_stances)


    # xleft, xright = ax.get_xlim()
    # ybottom, ytop = ax.get_ylim()
    # ax.set_aspect(abs((xright-xleft)/(ybottom-ytop)))

    # plt.show()


if __name__ == '__main__':
    if args.persist:
        full_pipeline.fit(X_train, y_train)
        joblib.dump(full_pipeline, 'models/ensemble.pkl')

    # from prediction import pred_lean
    # print(pred_lean(['tigeer']))
