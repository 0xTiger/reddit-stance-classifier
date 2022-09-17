# reddit-stance-classifier
A Flask webapp & Python scripts for predicting reddit users' political leaning, using their comment history. The backend is Flask with a PostgreSQL database which is queried using SQLAlchemy. 


## Usage
View the [live webapp](https://www.reddit-lean.com)

A model has been trained and pickled already in `models/ensemble.pkl`
If you wish to train your own model, first the postgres db must be set up and data added to it using `scraper.py`. 

`train_model.py` can then be run with various flags


## Model
Currently the only features this model uses are the frequency of comments made in different subreddits. 
A typical instance of data used for training looks like:
## Example instance of data
```json
"userMcUserFace01010101": {
  "stance": "libleft",
  "subs": {
    "rollercoasters": 1037,
    "CasualUK": 101,
    "PewdiepieSubmissions": 90,
    "polandball": 68,
    "unpopularopinion": 65,
    "todayilearned": 64,
    "LosAngeles": 62,
    "ShitAmericansSay": 53,
    "im14andthisisdeep": 53,
    "london": 32,
    "reclassified": 26,
    "TheRightCantMeme": 25,
    "CringeAnarchy": 22,
    "HongKong": 22,
    "MovieDetails": 22,
    "GenZ": 21,
  }
}
```
Here `"stance"` is the target data which we want to predict. This is encoded as a pair, mirroring the `"stance"`'s position on the political compass. The encoding is shown below:
```python
stancemap = {
  'libleft': (-1, -1), 
  'libright': (-1, 1), 
  'authleft': (1, -1), 
  'authright': (1, 1),
  'left': (0, -1),
  'right': (0, 1),
  'centrist': (0, 0),
  'auth': (1, 0),
  'lib': (-1, 0)
}
```

The target data are user flairs sampled from r/politicalcompassmemes. 

## Conclusion

As of writing a precision and recall of ~0.8 can be achieved on the unseen test set.
It is important to note however, that there may be significant selection bias as all instances of data are from users of r/politicalcompassmemes.
Therefore it remains to be seen whether this approach to identifying political positions will generalise to the Reddit population as a whole and make sensible predictions.

Due to the significant class imbalance present in the training data (the number of users that lean 'lib' on the v axis is far greater than those who lean 'auth'). It may be useful to consider alternative metrics such as bACC or PPCR.
