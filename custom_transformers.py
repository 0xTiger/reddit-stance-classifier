import pandas as pd
from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.feature_selection import chi2, f_classif
from math import log


def exclude_u_sub(k): return k[:2] != 'u_'


def scale(x): log(abs(x)+1)/log(2) * x/abs(x)


def multi_chi2(X, y):
    chisq_class1, p_class1 = chi2(X, y[:, 0])
    chisq_class2, p_class2 = chi2(X, y[:, 1])
    return chisq_class1 + chisq_class2, p_class1 + p_class2


def multi_f_classif(X, y):
    f_class1, p_class1 = f_classif(X, y[:, 0])
    f_class2, p_class2 = f_classif(X, y[:, 1])
    return f_class1 + f_class2, p_class1 + p_class2


class DictFilterer(BaseEstimator, TransformerMixin):
    def __init__(self, predicate):
        self.predicate = predicate
    def fit(self, X, y=None):
        return self
    def transform(self, X, y=None):
        return [{k:v for k, v in x.items() if self.predicate(k)} for x in X]


class ToSparseDF(BaseEstimator, TransformerMixin):
    def fit(self, X, y=None):
        return self
    def transform(self, X, y=None):
        return pd.DataFrame.sparse.from_spmatrix(X)
