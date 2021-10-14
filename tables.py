import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from pushlib_utils import stancemap_inv
import numpy as np

app = Flask(__name__)
app.config.from_object(os.environ['APP_SETTINGS'])
db = SQLAlchemy(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(32), unique=True)
    h_pos = db.Column(db.Float)
    v_pos = db.Column(db.Float)

    def __init__(self, username, v_pos, h_pos):
        self.username = username
        self.h_pos = h_pos
        self.v_pos = v_pos

    def stance_name(self, axis='both'):
        if axis == 'both': stance = stancemap_inv.get((round(self.v_pos), round(self.h_pos)))
        if axis == 'h': stance = stancemap_inv.get((0, round(self.h_pos)))
        if axis == 'v': stance = stancemap_inv.get((round(self.v_pos), 0))
        if axis == 'h_binary': stance = stancemap_inv.get((0, np.sign(self.h_pos)))
        if axis == 'v_binary': stance = stancemap_inv.get((np.sign(self.v_pos), 0))
        return stance

    def img(self):
        return self.stance_name() + '.png'

    @classmethod
    def from_name(cls, username):
        return cls.query.filter_by(username=username).first()


class Comment(db.Model):
    id = db.Column(db.String(10), primary_key=True)
    author = db.Column(db.String(32))
    body = db.Column(db.String(4096))
    subreddit = db.Column(db.String(32))
    score = db.Column(db.Integer)
    num_comments = db.Column(db.Integer)
    created_utc = db.Column(db.Integer)
    controversiality = db.Column(db.Integer)
    total_awards_received = db.Column(db.Integer)
 
    def __init__(self, 
                id,
                author,
                body,
                subreddit,
                score,
                num_comments,
                created_utc,
                controversiality,
                total_awards_received,
                **kwargs):
        self.id = id
        self.author = author
        self.body = body
        self.subreddit = subreddit
        self.score = score
        self.num_comments = num_comments
        self.created_utc = created_utc
        self.controversiality = controversiality
        self.total_awards_received = total_awards_received
 
