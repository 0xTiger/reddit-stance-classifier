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
from sklearn.feature_selection import SelectKBest, chi2
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import StratifiedShuffleSplit, cross_val_predict, GridSearchCV
from sklearn.metrics import confusion_matrix, precision_score, recall_score
from sklearn.base import BaseEstimator, TransformerMixin, clone
from sklearn.ensemble import RandomForestClassifier, VotingClassifier

class DictFilterer(BaseEstimator, TransformerMixin):
    def __init__(self, predicate):
        self.predicate = predicate
    def fit(self, X, y=None):
        return self
    def transform(self, X, y=None):
        return [{k:v for k, v in x.items() if self.predicate(k)} for x in X]

"""
The moral of the story of this project was that empty features columns (when in a sparse matrix)
break cross_val_predict and possibly other sklearn objects, throwing the error:
ValueError: Input contains NaN, infinity or a value too large for dtype('float64').

To solve this we construct a boolean ?Pandas? series:
(X_train != 0).any(axis=0) & (X_test != 0).any(axis=0)
that returns False if column is empty in either the train or test set.
We then select only the columns with value True

"""
"""
TODO
find best model:
best sofar: LinearSVC(C=100, loss='hinge', random_state=42)--
best sofar: RandomForestClassifier(min_samples_leaf=3, random_state=42)--
best sofar: VotingClassifier()--

Try different regularization (possibly less this time with larger dataset)
using GridSearchCV, also try giving more noteable users a greater sample_weight in .fit() method for the
make webapp backend to predict leaning given username
"""
with open('user_profiles.json') as f:
    mldata = json.load(f)

for user, data in mldata.items():
    if mldata[user]['stance'] in ['libright2', 'libright', 'right', 'authright']:
        mldata[user]['stance'] = 'R'
    if mldata[user]['stance'] in ['libleft', 'left', 'authleft']:
        mldata[user]['stance'] = 'L'

# if data['stance'] != 'None'
conditions = lambda user, data: data['stance'] in ['L', 'R'] and user != '[deleted]'
mldata = {user: data for user, data in mldata.items() if conditions(user, data)}

users = [user for user in mldata]
features = [data['subs'] for _, data in mldata.items()]
labels = [data['stance'] for _, data in mldata.items()]
stances = list(set(labels))


full_pipeline = Pipeline([('filterer', DictFilterer(lambda k: k[:2] != 'u_')), #k in rel_subs
                            ('vectorizer', DictVectorizer(sparse=True)),
                            ('selectKBest', SelectKBest(chi2, k=1000)),
                            ('scaler', StandardScaler(with_mean=False))])

X = full_pipeline.fit_transform(features, labels)

all = full_pipeline.named_steps.vectorizer.get_feature_names()
sel = full_pipeline.named_steps.selectKBest.get_support()
best_feat = np.array(all)[sel]
print(X.shape)
# print(best_feat)

X = pd.DataFrame.sparse.from_spmatrix(X, columns=best_feat, index=users)
y = pd.Series(labels)

ssplit = StratifiedShuffleSplit(n_splits=1, test_size=0.2, random_state=42)
for train_index, test_index in ssplit.split(X, y):
    X_train, y_train = X.iloc[train_index], y[train_index]
    X_test, y_test = X.iloc[test_index], y[test_index]


non_empty = (X_train != 0).any(axis=0) & (X_test != 0).any(axis=0)
print(non_empty.value_counts())
non_empty = non_empty.index[non_empty]

X_train = X_train[non_empty]
X_test = X_test[non_empty]

log_clf = LogisticRegression(C=0.2, penalty='l1')
forest_clf = RandomForestClassifier(min_samples_leaf=5, random_state=42)
voting_clf = VotingClassifier(estimators=[('forest', forest_clf), ('logit', log_clf)],
                                voting='soft')

y_pred = cross_val_predict(voting_clf, X_train, y_train, cv=5)

conf_mx = confusion_matrix(y_train, y_pred, labels=stances)

print(y_train.value_counts())
print(stances)
print(conf_mx)
print('Precision: ', precision_score(y_train, y_pred, average='weighted'))
print('Recall: ', recall_score(y_train, y_pred, average='weighted'))

fig, ax = plt.subplots()
cax = ax.matshow(conf_mx, cmap=plt.cm.gray)
fig.colorbar(cax)

ax.set_xticks(list(range(len(stances))))
ax.set_yticks(list(range(len(stances))))
ax.set_xticklabels(stances, rotation=45)
ax.set_yticklabels(stances)


xleft, xright = ax.get_xlim()
ybottom, ytop = ax.get_ylim()
ax.set_aspect(abs((xright-xleft)/(ybottom-ytop)))

plt.show()

voting_clf.fit(X_train, y_train)

log_ws = list(voting_clf.named_estimators_.logit.coef_[0])
for sub, weight in sorted(zip(X_train.columns, log_ws), key=lambda x: x[1]):
    print(sub, weight)

def pred_lean(names):
    dict = [get_subs(name) for name in names]
    series = full_pipeline.transform(dict)
    series = pd.DataFrame.sparse.from_spmatrix(series, columns=best_feat, index=names)
    series = series[non_empty]
    return voting_clf.predict(series)
#print(pred_lean(['tigeer']))
