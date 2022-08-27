from collections import Counter, defaultdict
from datetime import datetime, timedelta
from itertools import groupby
import hashlib

import httpagentparser
from requests.exceptions import HTTPError
from flask import render_template, request, redirect, url_for, session

from prediction import pred_lean
from utils import (
    stance_name_from_tuple,
    nested_list_to_table_html,
    get_user_data,
    get_comment_data,
    stancemap
)
from tables import User, Comment, Prediction, Traffic
from connections import db, app


def get_real_ip(r) -> str:
    return (r.environ['HTTP_X_FORWARDED_FOR'] 
        if r.environ.get('HTTP_X_FORWARDED_FOR') is not None
        else r.environ['REMOTE_ADDR'])


def get_analytics_data():
    userInfo = httpagentparser.detect(request.headers.get('User-Agent'), fill_none=True)
    time = datetime.now()
    if 'user' not in session:
        seed = f'{time}{request.remote_addr}'
        session['user'] = hashlib.md5(seed.encode('utf-8')).hexdigest()


    reqlog = Traffic(
        ip=get_real_ip(request),
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


def binned_counts(increment, value):
    since = datetime.now() - value * increment
    traffics = Traffic.query.with_entities(Traffic.timestamp).where(Traffic.timestamp > since).all()
    traffics = sorted(row[0] for row in traffics)
    
    incremental_traffic = [0]*value
    increment_idx = 0
    count = 0
    for ts in traffics:
        while ts > increment * increment_idx + since:
            incremental_traffic[increment_idx] = count
            count = 0
            increment_idx += 1
        count += 1
    return incremental_traffic


@app.route("/traffic")
def traffic():
    since = request.args.get('since', '24h')
    value, increment = int(since[:-1]), since[-1:]
    increment = {
        'd': timedelta(days=1),
        'h': timedelta(hours=1),
        'm': timedelta(minutes=1),
        's': timedelta(seconds=1),
    }.get(increment, 'h')
    
    traffic_frequency = binned_counts(increment, value)
    return render_template("traffic.html", 
        traffic_frequency=traffic_frequency,
        traffic_labels=[n for n in range(-len(traffic_frequency), 0)])


@app.route("/subreddits")
def subreddits():
    get_analytics_data()
    header = '</th><th>'.join(stancemap.keys())
    header = f'<thead><tr><th>Subreddit</th><th>{header}</th></tr></thead>'
    query = """
    SELECT * 
    FROM subreddit_stance
    WHERE subreddit_stance.subreddit = any(
        SELECT subreddit_stance.subreddit
        FROM subreddit_stance
        GROUP BY subreddit_stance.subreddit
        ORDER BY SUM(count) DESC
        LIMIT 100
    )
    """
    results = db.engine.execute(query)
    results = {name: defaultdict(int, {stance_name_from_tuple((y[2], y[1])): y[3] for y in group})
     for name, group in groupby(results, key=lambda x: x[0])}
    results = [[sub] + [result[stance] for stance in stancemap.keys()] for sub, result in results.items()]
    return render_template("subreddits.html", table=header + nested_list_to_table_html(results))


if __name__ == '__main__':
    app.debug = True
    app.run()
