from sklearn.base import BaseEstimator, TransformerMixin

def exclude_u_sub(k): return k[:2] != 'u_'

class DictFilterer(BaseEstimator, TransformerMixin):
    def __init__(self, predicate):
        self.predicate = predicate
    def fit(self, X, y=None):
        return self
    def transform(self, X, y=None):
        return [{k:v for k, v in x.items() if self.predicate(k)} for x in X]
