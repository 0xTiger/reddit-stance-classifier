import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from pushlib_utils import stancemap_inv
import numpy as np


app = Flask(__name__)
app.config.from_object(os.environ['APP_SETTINGS'])
db = SQLAlchemy(app)


class User(db.Model):
    name = db.Column(db.String(32), primary_key=True, unique=True)
    created_utc = db.Column(db.Integer)
    total_karma = db.Column(db.Integer)
    link_karma = db.Column(db.Integer)
    comment_karma = db.Column(db.Integer)
    awardee_karma = db.Column(db.Integer)
    awarder_karma = db.Column(db.Integer)
    has_verified_email = db.Column(db.Boolean)
    verified = db.Column(db.Boolean)
    is_gold = db.Column(db.Boolean)
    is_mod = db.Column(db.Boolean)
    is_employee = db.Column(db.Boolean)
    comments = db.relationship('Comment', backref='user')
    pred = db.relationship('Prediction', backref='user', uselist=False)

    def __init__(self, 
                 name,
                 created_utc,
                 total_karma,
                 link_karma,
                 comment_karma,
                 awardee_karma,
                 awarder_karma,
                 has_verified_email,
                 verified,
                 is_gold,
                 is_mod,
                 is_employee,
                 **kwargs):
        self.name = name
        self.created_utc = created_utc
        self.total_karma = total_karma
        self.link_karma = link_karma
        self.comment_karma = comment_karma
        self.awardee_karma = awardee_karma
        self.awarder_karma = awarder_karma
        self.has_verified_email = has_verified_email
        self.verified = verified
        self.is_gold = is_gold
        self.is_mod = is_mod
        self.is_employee = is_employee

    @classmethod
    def from_name(cls, name):
        return cls.query.filter_by(name=name).first()


class Prediction(db.Model):
    name = db.Column(db.String(32), db.ForeignKey('user.name'), primary_key=True, unique=True)
    h_pos = db.Column(db.Float)
    v_pos = db.Column(db.Float)

    def __init__(self, name, v_pos, h_pos):
        self.name = name
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


class Comment(db.Model):
    id = db.Column(db.String(10), primary_key=True)
    author = db.Column(db.String(32), db.ForeignKey('user.name'))
    body = db.Column(db.String(4096))
    link_title = db.Column(db.String(2048))
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
                 link_title,
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
        self.link_title = link_title
        self.subreddit = subreddit
        self.score = score
        self.num_comments = num_comments
        self.created_utc = created_utc
        self.controversiality = controversiality
        self.total_awards_received = total_awards_received
 
