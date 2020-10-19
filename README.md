# reddit-stance-classifier
A Flask webapp & Python scripts for predicting reddit users' political leaning, using their comment history.


### usage
View the [live webapp](https://www.reddit-lean.com)

Alternatively: Run one of the classifiers from the command line using the interactive shell option and call `pred_lean`

```python3
\reddit-stance-classifier>python
>>>from prediction import pred_lean
>>>pred_lean('userMcUserFace01010101')
('L', 'L', 0.821243598285102, 0.893544755401233)
```
The tuple returned is of the form `(h_stance, v_stance, h_confidence, v_confidence)`


### example instance of data
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

In this example the `"subs"` from this instance of data would be encoded into a sparse array and passed into the model as features.
The model that has subsequently been trained to predict `"stance"` would then make a prediction for this new instance of data.


### conclusion

As of writing a precision and recall of ~0.8 can be achieved on the unseen test set.
It is important to note however, that there may be significant selection bias as all instances of data are from users of r/politicalcompassmemes.
Therefore it remains to be seen whether this approach to identifying political positions will generalise to the Reddit population as a whole and make sensible predictions.

Due to the significant class imbalance present in the training data (the number of users that lean 'lib' on the v axis is far greater than those who lean 'auth'). It may be useful to consider alternative metrics such as bACC or PPCR.
