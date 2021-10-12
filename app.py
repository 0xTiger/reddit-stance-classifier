import os
from flask import Flask, render_template, request, redirect, url_for
from dash import Dash
from flask_sqlalchemy import SQLAlchemy
from prediction import pred_lean
from requests.exceptions import HTTPError
from tables import User
from dashapp_layout import layout

app = Flask(__name__)
dashapp = Dash(__name__, server=app, url_base_pathname='/plots/')
app.config.from_object(os.environ['APP_SETTINGS'])
db = SQLAlchemy(app)


@app.route("/")
def index():
    return render_template("home.html")


@app.route("/pred", methods=['POST', 'GET'])
def success():
    if request.method == 'POST':
        username = request.form['username']
        if not username:
            return render_template("failure.html", error='Please enter a username')
        # Check if user is cached
        current_user = User.from_name(username)
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
                                                h_confidence=f'{abs(current_user.h_pos):.0%}',
                                                v_confidence=f'{abs(current_user.v_pos):.0%}')
    elif request.method == 'GET':
        return redirect(url_for('index'))


@app.route("/about")
def about():
    return render_template("about.html")


if __name__ == '__main__':
    app.debug = True
    dashapp.layout = layout
    app.run()
