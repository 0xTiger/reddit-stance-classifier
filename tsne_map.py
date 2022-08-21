import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.cm as cm
from sklearn.feature_extraction import DictVectorizer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import Normalizer
from sklearn.decomposition import TruncatedSVD
from sklearn.manifold import TSNE
from sklearn.cluster import DBSCAN

from tables import Comment, Stance, db
from collections import defaultdict

comment_groups = (
    Comment.query
    .with_entities(Comment.author, Comment.subreddit, db.func.count(Comment.subreddit))
    .group_by(Comment.author, Comment.subreddit)
    .iterator()
)
stances = Stance.query.iterator()

stance_dict = dict()
subreddit_counts = defaultdict(dict)
for author, subreddit, count in comment_groups:
    subreddit_counts[author][subreddit] = count
for stance in stances:
    stance_dict[stance.name] = (stance.v_pos, stance.h_pos)

features, labels = [], []
for author, subs in subreddit_counts.items():
    label = stance_dict.get(author)
    if label:
        features.append(subs)
        labels.append(label)

labels = np.array(labels)
features = pd.Series(features)

v = DictVectorizer(sparse=True)
X = v.fit_transform([x for x in features])

lr = np.array([x[1] if x is not None else 0 for x in labels])

subreddits = v.get_feature_names_out()
subreddit_comments = X.sum(axis=0).getA1()
subreddit_commenters = (X > 0).sum(axis=0).getA1()

n = 1_000
XT = X.T[subreddit_commenters > n]
XT = XT.multiply(1 / XT.sum(axis=0).getA1()) # Weight everyone equally, democracy baby!

estimator = Pipeline([
    ('SVD', TruncatedSVD(n_components=64)),
    ('TSNE', TSNE(perplexity=100, n_iter=10_000, metric='cosine', n_jobs=-1, verbose=1))
])
embed = estimator.fit_transform(XT)


dbscan = DBSCAN(min_samples=2, eps=0.25)
clusters = dbscan.fit_predict(embed)
fig, ax = plt.subplots(figsize=(30,30))
x = embed[:, 0]
y = embed[:, 1]
ax.scatter(x, y,
    alpha=0.5,
    s=subreddit_commenters[subreddit_commenters > n] ** 0.66 / 2,
    c=Normalizer(norm='l1').fit_transform(XT) @lr,
    cmap=cm.seismic
)

txts = subreddits[subreddit_commenters > n]
for subreddit_idx in np.argwhere(clusters == -1).ravel():
    ax.annotate(
        txts[subreddit_idx], 
        (x[subreddit_idx], y[subreddit_idx]), 
        fontsize=8,
        va='center'
    )
for cluster in range(clusters.max()):
    subreddit_idxs = np.argwhere(clusters == cluster).ravel()
    ax.annotate(
        '\n'.join(txts[subreddit_idxs]), 
        (x[subreddit_idxs].mean(), y[subreddit_idxs].mean()),
        fontsize=8,
        va='center'
    )
ax.set_xticks([])
ax.set_yticks([])
ax.set_title('Map of Reddit (Political)\n', fontsize=64)
fig.savefig('test.png')
