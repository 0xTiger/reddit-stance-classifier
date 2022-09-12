import argparse
from timeit import default_timer as timer

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.lines as mlines
import joblib
from sklearn.feature_extraction import DictVectorizer
from sklearn.feature_selection import SelectKBest
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import StratifiedShuffleSplit, cross_val_predict
from sklearn.metrics import confusion_matrix, precision_score, recall_score, mean_absolute_error
from sklearn.ensemble import RandomForestRegressor
from sklearn.multioutput import MultiOutputRegressor

from custom_transformers import DictFilterer, ToSparseDF, exclude_u_sub, multi_f_classif
from utils import stancecolormap, stancemap, stance_name_from_tuple


parser = argparse.ArgumentParser()
parser.add_argument('-p', '--persist', action='store_true', help='Specify whether to make the model persistent in models/*')
parser.add_argument('--noval', action='store_true', help='specify whether to evaluate the model\'s performance')
args = parser.parse_args()

forest_clf = RandomForestRegressor(min_samples_leaf=5, random_state=42)
multi_clf = MultiOutputRegressor(forest_clf)
full_pipeline = Pipeline([
    ('filterer', DictFilterer(exclude_u_sub)),
    ('vectorizer', DictVectorizer(sparse=True)),
    ('selectKBest', SelectKBest(multi_f_classif, k=1000)),
    ('scaler', StandardScaler(with_mean=False)),
    ('framer', ToSparseDF()),
    ('clf', multi_clf)
])

if __name__ == '__main__':
    from tables import Comment, Stance, db
    from collections import defaultdict

    comment_groups = (
        Comment.query
        .with_entities(Comment.author, Comment.subreddit, db.func.count(Comment.subreddit))
        .group_by(Comment.author, Comment.subreddit)
        .all()
    )
    stances = Stance.query.all()

    stances_dict = dict()
    subreddit_counts = defaultdict(dict)
    for author, subreddit, count in comment_groups:
        subreddit_counts[author][subreddit] = count
    for stance in stances:
        stances_dict[stance.name] = (stance.v_pos, stance.h_pos)

    features, labels = [], []
    for author, subs in subreddit_counts.items():
        label = stances_dict.get(author)
        if label:
            features.append(subs)
            labels.append(label)

    labels = np.array(labels)
    features = pd.Series(features)

    splitter = StratifiedShuffleSplit(n_splits=1, test_size=0.2, random_state=42)
    for train_index, test_index in splitter.split(features, labels):
        X_train, y_train = features[train_index], labels[train_index]
        X_test, y_test = features[test_index], labels[test_index]

    if not args.noval:
        start = timer()
        y_pred = cross_val_predict(full_pipeline, X_train, y_train, cv=5, n_jobs=-1)
        y_pred = y_pred.clip(-1, 1)
        end = timer()
        print(f'Trained in {end - start}')
        print(f'MAE: {mean_absolute_error(y_train, y_pred)}')
        stances = sorted(stancemap.keys())

        actual_stances, pred_stances, conf_matrices, precision_scores, recall_scores = dict(), dict(), dict(), dict(), dict()
        for axis in ['both', 'h_binary', 'v_binary']:
            if axis == 'h_binary':
                relevant_idx = y_train[:, 1] != 0
            elif axis == 'v_binary':
                relevant_idx = y_train[:, 0] != 0
            else:
                relevant_idx = np.ones_like(y_train[:, 0], dtype=bool)

            actual_stances[axis] = np.array(list(map(lambda t: stance_name_from_tuple(t, axis=axis), y_train[relevant_idx])))
            pred_stances[axis] = np.array(list(map(lambda t: stance_name_from_tuple(t, axis=axis), y_pred[relevant_idx])))
            conf_matrices[axis] = confusion_matrix(actual_stances[axis], pred_stances[axis])    
            precision_scores[axis] = precision_score(actual_stances[axis], pred_stances[axis], average='weighted')
            recall_scores[axis] = recall_score(actual_stances[axis], pred_stances[axis], average='weighted')

            print(np.unique(actual_stances[axis]))
            print(conf_matrices[axis])
            print(f'Precision: {precision_scores[axis]}')
            print(f'Recall: {recall_scores[axis]}')
        
        fig, ax = plt.subplots()
        cax = ax.matshow(conf_matrices['both'], cmap=plt.cm.gray)
        fig.colorbar(cax)

        ax.set_xticks(list(range(len(stances))))
        ax.set_yticks(list(range(len(stances))))
        ax.set_xticklabels(stances, rotation=45)
        ax.set_yticklabels(stances)


        xleft, xright = ax.get_xlim()
        ybottom, ytop = ax.get_ylim()
        ax.set_aspect(abs((xright-xleft)/(ybottom-ytop)))
        

        fig2, ax2 = plt.subplots()
        ax2.scatter(
            y_pred[:, 1],
            y_pred[:, 0],
            color=[stancecolormap.get(stance) for stance in actual_stances['both']],
            s=5,
            alpha=0.5
        )
        ax2.axhline(0, color='k', linestyle='--')
        ax2.axvline(0, color='k', linestyle='--')
        ax2.set_xlabel('Left/Right')
        ax2.set_ylabel('Lib/Auth')
        ax2.set_aspect(abs((xright-xleft)/(ybottom-ytop)))

        ax2.legend(handles=[mlines.Line2D([], [], color=color, marker='.', linestyle='None',
                            markersize=4, label=stance) for stance,color in stancecolormap.items()],
                    bbox_to_anchor=(1.04,1), loc="upper left")
        plt.show()

    if args.persist:
        full_pipeline.fit(X_train, y_train)
        joblib.dump(full_pipeline, 'models/ensemble.pkl')
