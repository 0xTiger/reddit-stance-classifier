import os
from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from prediction import pred_lean
from requests.exceptions import HTTPError
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

        stancemap = {'libleft': (-1, -1), 
                'libright': (-1, 1), 
                'authleft': (1, -1), 
                'authright': (1, 1),
                'left': (0, -1),
                'right': (0, 1),
                'centrist': (0, 0),
                'auth': (1, 0),
                'lib': (-1, 0)}

        stancemap_inv = {v:k for k,v in stancemap.items()}

        if axis == 'both': stance = stancemap_inv.get((round(self.v_pos), round(self.h_pos)))
        if axis == 'h': stance = stancemap_inv.get((0, round(self.h_pos)))
        if axis == 'v': stance = stancemap_inv.get((round(self.v_pos), 0))
        if axis == 'h_binary': stance = stancemap_inv.get((0, np.sign(self.h_pos)))
        if axis == 'v_binary': stance = stancemap_inv.get((np.sign(self.v_pos), 0))
        return stance


    def img(self):
        return self.stance_name() + '.png'

@app.route("/")
def index():
    return render_template("home.html")

@app.route("/pred", methods=['POST', 'GET'])
def success():
    if request.method == 'POST':
        username = request.form['username']
        if not username:
            return render_template("failure.html", error='Please enter a username')
        # check if user is cached
        current_user = User.query.filter_by(username=username).first()
        if not current_user:
            try:
                pred_stance = pred_lean(username)
            except ValueError as err:
                return render_template("failure.html", error=str(err))
            except HTTPError as err:
                return render_template("failure.html", error='External API error')

            current_user = User(username, *pred_stance)
            db.session.add(current_user)
            db.session.commit()

        return render_template("success.html", stance_name=current_user.stance_name(),
                                                user=username,
                                                img=current_user.img(),
                                                h_fullstance= current_user.stance_name(axis='h_binary'),
                                                v_fullstance= current_user.stance_name(axis='v_binary'),
                                                h_confidence=f'{current_user.h_pos:.0%}',
                                                v_confidence=f'{current_user.v_pos:.0%}')
    elif request.method == 'GET':
        return redirect(url_for('index'))

@app.route("/about")
def about():
    return render_template("about.html")

if __name__ == '__main__':
    app.debug = True
    app.run()
