from flask import Flask, render_template, request
from flask_sqlalchemy import SQLAlchemy
from prediction import pred_lean

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:dbpass@localhost/reddit_stance_classifier'
db = SQLAlchemy(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(32), unique=True)
    stance = db.Column(db.String(16))

    def __init__(self, username, stance):
        self.username = username
        self.stance = stance

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/pred", methods=['POST'])
def success():
    if request.method == 'POST':
        username = request.form['username']
        if not username:
            return render_template("failure.html", error='Please enter a username')
        cached_user = User.query.filter_by(username=username).first()
        if cached_user:
            stance = cached_user.stance
        else:
            try:
                pred_stance = pred_lean(username)
            except ValueError as err:
                return render_template("failure.html", error=str(err))

            new_user = User(username, pred_stance)
            db.session.add(new_user)
            db.session.commit()

            stance = new_user.stance
    return render_template("success.html", stance=stance, user=username)

if __name__ == '__main__':
    app.debug = True
    app.run()
