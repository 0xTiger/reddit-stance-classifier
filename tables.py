from utils import stancemap, stance_name_from_tuple
from connections import db


class User(db.Model):
    name = db.Column(db.String, primary_key=True, unique=True)
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
    searches = db.Column(db.Integer)
    comments = db.relationship('Comment', backref='user', cascade = "all, delete, delete-orphan")
    prediction = db.relationship('Prediction', backref='user', uselist=False, cascade = "all, delete, delete-orphan")
    stance = db.relationship('Stance', backref='user', uselist=False, cascade = "all, delete, delete-orphan")

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
        self.searches = 0

    @classmethod
    def from_name(cls, name):
        # Case insensitive search since Reddit usernames technically are
        return cls.query.filter(db.func.lower(cls.name) == db.func.lower(name)).first()


class Prediction(db.Model):
    name = db.Column(db.String, db.ForeignKey('user.name'), primary_key=True, unique=True)
    h_pos = db.Column(db.Float)
    v_pos = db.Column(db.Float)

    def __init__(self, name, v_pos, h_pos):
        self.name = name
        self.h_pos = h_pos
        self.v_pos = v_pos

    def stance_name(self, axis='both'):
        return stance_name_from_tuple((self.v_pos, self.h_pos), axis=axis)

    def img(self):
        return self.stance_name() + '.png'


class Stance(db.Model):
    name = db.Column(db.String, db.ForeignKey('user.name'), primary_key=True, unique=True)
    h_pos = db.Column(db.Integer)
    v_pos = db.Column(db.Integer)

    def __init__(self, name, v_pos, h_pos):
        self.name = name
        self.h_pos = h_pos
        self.v_pos = v_pos

    def stance_name(self, axis='both'):
        return stance_name_from_tuple((self.v_pos, self.h_pos), axis=axis)

    def img(self):
        return self.stance_name() + '.png'

    @classmethod
    def from_str(cls, username, stance_name):
        return cls(username, *stancemap[stance_name])


class Comment(db.Model):
    id = db.Column(db.String, primary_key=True)
    author = db.Column(db.String, db.ForeignKey('user.name'))
    body = db.Column(db.String)
    link_title = db.Column(db.String)
    subreddit = db.Column(db.String)
    score = db.Column(db.Integer)
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
                 created_utc,
                 controversiality,
                 total_awards_received,
                 **kwargs):
        self.id = id
        self.author = author.replace('\x00', '\uFFFD')
        self.body = body.replace('\x00', '\uFFFD')
        self.link_title = link_title.replace('\x00', '\uFFFD')
        self.subreddit = subreddit.replace('\x00', '\uFFFD')
        self.score = score
        self.created_utc = created_utc
        self.controversiality = controversiality
        self.total_awards_received = total_awards_received


class Traffic(db.Model):
    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    ip = db.Column(db.String)
    os = db.Column(db.String)
    browser = db.Column(db.String)
    session_id = db.Column(db.String)
    path = db.Column(db.String)
    method = db.Column(db.String)
    timestamp = db.Column(db.DateTime)

    def __init__(self, ip, os, browser, session_id, path, method, timestamp):
        self.ip = ip
        self.os = os
        self.browser = browser
        self.session_id = session_id
        self.path = path
        self.method = method
        self.timestamp = timestamp