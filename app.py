from flask import Flask, render_template, request
from flask_sqlalchemy import SQLAlchemy
#from stance_clf_ensemble import pred_lean
import random
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

@app.route("/success", methods=['POST'])
def success():
    if request.method == 'POST':
        POST_username = request.form['username']

        cached_user = User.query.filter_by(username=POST_username).first()
        if cached_user:
            stance = cached_user.stance
        else:
            new_user = User(POST_username, random.choice(['L', 'R', 'C']))
            db.session.add(new_user)
            db.session.commit()

            stance = new_user.stance
    return render_template("index.html", text='Stance: ' + stance)

if __name__ == '__main__':
    app.debug = True
    app.run()
