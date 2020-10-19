import json
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from pushlib_utils import get_subs
def warn(*args, **kwargs):
    pass
import warnings
warnings.warn = warn
from sklearn.feature_extraction import DictVectorizer
from custom_transformers import DictFilterer, ToSparseDF, exclude_u_sub
from sklearn.feature_selection import SelectKBest, chi2
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import StratifiedShuffleSplit, cross_val_predict, GridSearchCV
from sklearn.metrics import confusion_matrix, precision_score, recall_score
from sklearn.ensemble import RandomForestClassifier, VotingClassifier
from sklearn.base import clone
import joblib


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

users, features, labels = [], [], []
users2, features2, labels2 = [], [], []
for user, data in gen:

    if mldata[user]['stance'] in ['libleft', 'left', 'authleft']:
        mldata[user]['h_stance'] = 'L'
    if mldata[user]['stance'] in ['libright', 'libright2', 'right', 'authright']:
        mldata[user]['h_stance'] = 'R'

    if mldata[user]['stance'] in ['authleft', 'auth', 'authright']:
        mldata[user]['v_stance'] = 'A'
    if mldata[user]['stance'] in ['libleft', 'lib', 'libright']:
        mldata[user]['v_stance'] = 'L'

    if 'h_stance' in mldata[user]:
        users.append(user)
        features.append(mldata[user]['subs'])
        labels.append(mldata[user]['h_stance'])

    if 'v_stance' in mldata[user]:
        users2.append(user)
        features2.append(mldata[user]['subs'])
        labels2.append(mldata[user]['v_stance'])


h_stances = list(set(labels))
v_stances = list(set(labels2))


full_pipeline = Pipeline([('filterer', DictFilterer(exclude_u_sub)), #k in rel_subs
                            ('vectorizer', DictVectorizer(sparse=True)),
                            ('selectKBest', SelectKBest(chi2, k=1000)),
                            ('scaler', StandardScaler(with_mean=False)),
                            ('framer', ToSparseDF())])
full_pipeline2 = clone(full_pipeline)

X = full_pipeline.fit_transform(features, labels)
X2 = full_pipeline2.fit_transform(features2, labels2)
y = pd.Series(labels)
y2 = pd.Series(labels2)

print(X.shape)

splitter = StratifiedShuffleSplit(n_splits=1, test_size=0.2, random_state=42)
for train_index, test_index in splitter.split(X, y):
    X_train, y_train = X.iloc[train_index], y[train_index]
    X_test, y_test = X.iloc[test_index], y[test_index]

splitter2 = StratifiedShuffleSplit(n_splits=1, test_size=0.2, random_state=42)
for train_index, test_index in splitter2.split(X2, y2):
    X_train2, y_train2 = X2.iloc[train_index], y2[train_index]
    X_test2, y_test2 = X2.iloc[test_index], y2[test_index]

log_clf = LogisticRegression(C=0.2, penalty='l1', solver='liblinear')
forest_clf = RandomForestClassifier(min_samples_leaf=5, random_state=42)
voting_clf = VotingClassifier(estimators=[('forest', forest_clf), ('logit', log_clf)],
                                voting='soft')
voting_clf2 = clone(voting_clf)

if __name__ == '__main__':
    y_pred = cross_val_predict(voting_clf, X_train, y_train, cv=5)
    y_pred2 = cross_val_predict(voting_clf2, X_train2, y_train2, cv=5)

    conf_mx = confusion_matrix(y_train, y_pred, labels=h_stances)
    conf_mx2 = confusion_matrix(y_train2, y_pred2, labels=v_stances)

    print(y_train.value_counts())
    print(h_stances)
    print(conf_mx)
    print('Precision: ', precision_score(y_train, y_pred, average='weighted'))
    print('Recall: ', recall_score(y_train, y_pred, average='weighted'))

    print(y_train2.value_counts())
    print(v_stances)
    print(conf_mx2)
    print('Precision: ', precision_score(y_train2, y_pred2, average='weighted'))
    print('Recall: ', recall_score(y_train2, y_pred2, average='weighted'))

    fig, ax = plt.subplots()
    cax = ax.matshow(conf_mx, cmap=plt.cm.gray)
    fig.colorbar(cax)

    ax.set_xticks(list(range(len(h_stances))))
    ax.set_yticks(list(range(len(h_stances))))
    ax.set_xticklabels(h_stances, rotation=45)
    ax.set_yticklabels(h_stances)


    xleft, xright = ax.get_xlim()
    ybottom, ytop = ax.get_ylim()
    ax.set_aspect(abs((xright-xleft)/(ybottom-ytop)))

    plt.show()

voting_clf.fit(X_train, y_train)
voting_clf2.fit(X_train2, y_train2)
if __name__ == '__main__':
    log_ws = list(voting_clf.named_estimators_.logit.coef_[0])
    for sub, weight in sorted(zip(X_train.columns, log_ws), key=lambda x: x[1]):
        print(sub, weight)

    joblib.dump(voting_clf, 'models/clf_ensemble.pkl')
    joblib.dump(full_pipeline, 'models/pipeline_ensemble.pkl')
    joblib.dump(voting_clf2, 'models/clf_ensemble2.pkl')
    joblib.dump(full_pipeline2, 'models/pipeline_ensemble2.pkl')

from prediction import pred_lean
#print(pred_lean(['tigeer']))
