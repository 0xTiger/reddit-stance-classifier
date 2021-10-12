from flask import Flask
app = Flask(__name__)

from flask_sqlalchemy import SQLAlchemy
db = SQLAlchemy(app)
from pushlib_utils import stancemap_inv
import numpy as np


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
