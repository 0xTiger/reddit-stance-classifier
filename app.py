import os
from flask import Flask, render_template, request
from flask_sqlalchemy import SQLAlchemy
from prediction import pred_lean

app = Flask(__name__)

app.config.from_object(os.environ['APP_SETTINGS'])
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

quadrant_map = {'L': ('left.png', 'left'),
                'R': ('right.png', 'right')}

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(32), unique=True)
    stance = db.Column(db.String(16))
    confidence = db.Column(db.Float)

    def __init__(self, username, stance, confidence):
        self.username = username
        self.stance = stance
        self.confidence = confidence

@app.route("/")
def index():
    return render_template("home.html")

@app.route("/pred", methods=['POST'])
def success():
    if request.method == 'POST':
        username = request.form['username']
        if not username:
            return render_template("failure.html", error='Please enter a username')
        cached_user = User.query.filter_by(username=username).first()
        if cached_user:
            stance = cached_user.stance
            confidence = cached_user.confidence
        else:
            try:
                pred_stance, confidence = pred_lean(username)
            except ValueError as err:
                return render_template("failure.html", error=str(err))

            new_user = User(username, pred_stance, confidence)
            db.session.add(new_user)
            db.session.commit()

            stance = new_user.stance
            confidence = new_user.confidence

        stance_img, stance_name = quadrant_map[stance]
    return render_template("success.html", stance_name=stance_name,
                                            user=username,
                                            img=stance_img,
                                            confidence=f'{confidence*100:.0f}%' + ' (LOW)' if confidence < 0.7 else f'{confidence*100:.0f}%')

@app.route("/about")
def about():
    return render_template("about.html")

if __name__ == '__main__':
    app.debug = True
    app.run()
