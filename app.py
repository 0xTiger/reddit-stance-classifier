import os
from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from prediction import pred_lean
from requests.exceptions import HTTPError


app = Flask(__name__)

app.config.from_object(os.environ['APP_SETTINGS'])
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(32), unique=True)

    h_stance = db.Column(db.String(1))
    h_confidence = db.Column(db.Float)

    v_stance = db.Column(db.String(1))
    v_confidence = db.Column(db.Float)

    def __init__(self, username, h_stance, v_stance, h_confidence, v_confidence):
        self.username = username
        self.h_stance = h_stance
        self.h_confidence = h_confidence
        self.v_stance = v_stance
        self.v_confidence = v_confidence

    def stance_name(self):

        quadrant_map = {'-L' : 'left',
                        '--': 'unknown',
                        '-R': 'right',
                        'A-': 'auth',
                        'L-': 'lib',
                        'LL': 'libleft',
                        'LR': 'libright',
                        'AL': 'authleft',
                        'AR': 'authright'}
        return quadrant_map[(self.v_stance if (self.v_confidence > 0.6) else '-') + (self.h_stance if (self.h_confidence > 0.6) else '-')]

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
                                                h_fullstance= 'left' if current_user.h_stance == 'L' else 'right',
                                                v_fullstance= 'lib' if current_user.v_stance == 'L' else 'auth',
                                                h_confidence=f'{current_user.h_confidence:.0%}',
                                                v_confidence=f'{current_user.v_confidence:.0%}')
    elif request.method == 'GET':
        return redirect(url_for('index'))

@app.route("/about")
def about():
    return render_template("about.html")

if __name__ == '__main__':
    app.debug = True
    app.run()
