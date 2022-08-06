from collections import Counter
from datetime import datetime, timedelta
import hashlib

import httpagentparser
from requests.exceptions import HTTPError
from flask import render_template, request, redirect, url_for, session

from prediction import pred_lean
from utils import get_user_data, get_comment_data
from tables import User, Comment, Prediction, Traffic
from connections import db, app
    

def get_analytics_data():
    userInfo = httpagentparser.detect(request.headers.get('User-Agent'))
    time = datetime.now()
    if 'user' not in session:
        seed = f'{time}{request.remote_addr}'
        session['user'] = hashlib.md5(seed.encode('utf-8')).hexdigest()

    reqlog = Traffic(
        ip=request.remote_addr,
        os=userInfo['platform']['name'],
        browser=userInfo['browser']['name'],
        session_id=session['user'],
        path=request.path,
        method=request.method,
        timestamp=time,
    )
    db.session.add(reqlog)
    db.session.commit()


@app.route("/")
def index():
    get_analytics_data()
    return render_template("home.html")


@app.route("/pred", methods=['POST', 'GET'])
def success():
    get_analytics_data()
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
    get_analytics_data()
    return render_template("about.html")

@app.route("/traffic")
def traffic():
    traffics = Traffic.query.where(Traffic.timestamp > datetime.now() - timedelta(days=1)).all()
    hourly_counts = Counter(traffic.timestamp.hour for traffic in traffics)
    traffic_frequency = [hourly_counts.get(hour, 0) for hour in range(24)]
    return render_template("traffic.html", 
        traffic_frequency=traffic_frequency)

if __name__ == '__main__':
    app.debug = True
    app.run()
