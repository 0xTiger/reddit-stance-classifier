from flask import render_template, request, redirect, url_for
from prediction import pred_lean
from requests.exceptions import HTTPError
from utils import get_user_data, get_comment_data
from tables import User, Comment, Prediction
from connections import db, app

@app.route("/")
def index():
    return render_template("home.html")


@app.route("/pred", methods=['POST', 'GET'])
def success():
    if request.method == 'POST':
        username = request.form['username']
        if not username:
            return render_template("failure.html", error='Please enter a username')
        # Check if user is in db
        user = User.from_name(username)
        if not user:
            try:
                user_data = get_user_data(username)
                comments_data = get_comment_data(username)
            except HTTPError as err:
                if err.response.status_code == 404:
                    return render_template("failure.html", error=f'User \'{username}\' does not exist')
                return render_template("failure.html", error='External API error')

            user = User(**user_data)
            user.comments = [Comment(**comment_data) for comment_data in comments_data]
            user.prediction = pred_lean(user)
            
            db.session.add(user)

        user.searches += 1
        if not user.prediction:
            user.prediction = pred_lean(user)
        db.session.commit()

        return render_template("success.html", 
                                user=user,
                                h_confidence=f'{abs(user.prediction.h_pos):.0%}',
                                v_confidence=f'{abs(user.prediction.v_pos):.0%}')

    elif request.method == 'GET':
        return redirect(url_for('index'))


@app.route("/about")
def about():
    return render_template("about.html")


if __name__ == '__main__':
    app.debug = True
    app.run()
