from collections import defaultdict
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
    stancemap,
    stancecolormap
)
from tables import User, Comment, Traffic
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

        return render_template(
            "success.html",
            user=user,
            h_confidence=f'{abs(user.prediction.h_pos):.0%}',
            v_confidence=f'{abs(user.prediction.v_pos):.0%}'
        )

    elif request.method == 'GET':
        return redirect(url_for('index'))


@app.route("/about")
def about():
    get_analytics_data()
    return render_template("about.html")


def binned_counts(increment, value, traffics):
    since = datetime.now() - value * increment
    incremental_traffic = [0]*value
    increment_idx = 0
    count = 0
    for ts in traffics:
        while ts > increment * (increment_idx + 1) + since:
            incremental_traffic[increment_idx] = count
            count = 0
            increment_idx += 1
        count += 1
    incremental_traffic[increment_idx] = count
    return incremental_traffic


def get_traffic_data(increment, value):
    since = datetime.now() - value * increment
    traffics = (
        Traffic.query.with_entities(Traffic.timestamp, Traffic.path)
        .where(Traffic.timestamp > since)
        .order_by(Traffic.timestamp)
        .all()
    )
    grouped_traffics = groupby(sorted(traffics, key=lambda x: x[1]), key=lambda x: x[1])
    
    incremental_traffic = {
        path: binned_counts(increment, value, (t[0] for t in group)) 
            for path, group in grouped_traffics
    }
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
    
    available_colors = ['grey', 'red', 'blue', 'green', 'yellow', 'orange']
    traffic_frequency = get_traffic_data(increment, value)
    datasets = [
        {
            'label': path, 
            'data': traffics, 
            'fill': '-1' if i else 'origin', 
            'borderColor': available_colors[i % len(available_colors)], 
            'backgroundColor': available_colors[i % len(available_colors)]
        }
        for i, (path, traffics) in enumerate(traffic_frequency.items())
    ]
    return render_template("traffic.html", 
        traffic_frequency=datasets,
        traffic_labels=[n for n in range(-value, 0)])


@app.route("/subreddits", methods=['POST', 'GET'])
def subreddits():
    get_analytics_data()
    if request.method == 'POST':
        subreddit = request.form['subreddit']
    else:
        subreddit = ''
    query = """
    SELECT * 
    FROM subreddit_stance
    WHERE subreddit_stance.subreddit = any(
        SELECT subreddit_stance.subreddit
        FROM subreddit_stance
        WHERE subreddit_stance.subreddit ILIKE %s
        GROUP BY subreddit_stance.subreddit
        ORDER BY SUM(count) DESC
        LIMIT 100
    )
    """
    results = db.engine.execute(query, f'%%{subreddit}%%')
    results = {name: defaultdict(int, {stance_name_from_tuple((y[2], y[1])): y[3] for y in group})
     for name, group in groupby(results, key=lambda x: x[0])}
    # results = [[sub] + [f'<p style="color: {stancecolormap[stance]}">{result[stance] / sum(result.values()):.0%}</p>' for stance in stancemap.keys()] for sub, result in results.items()]
    def div_from_stance_pct(pct, stance):
        #https://stackoverflow.com/a/34074407/19264346 for no width content
        return f"<div style='background-color:{stancecolormap[stance]}; width:{pct * 100}%; float:left;'>&nbsp;</div>"
    def div_from_sub(sub):
        return f'<a href="https://reddit.com/r/{sub}" target="_blank">{sub}</a>'
    sorted_results = sorted(results.items(), key=lambda x: sum(x[1].values()), reverse=True)
    
    results = [[div_from_sub(sub)] + [''.join(div_from_stance_pct(result[stance] / sum(result.values()), stance) for stance in stancemap.keys())] for sub, result in sorted_results]
    stance_legend = ''.join(f'<div style="background-color:{colour}">{stance}</div>' for stance, colour in stancecolormap.items())
    tooltip = f'<div class="tooltip"><i class="fas fa-info-circle"></i><span class="tooltiptext">{stance_legend}</span></div>'
    header = f'<thead><tr><th>Subreddit</th><th>{tooltip} Demographics </th></tr></thead>'
    return render_template("subreddits.html", table=header + nested_list_to_table_html(results))


if __name__ == '__main__':
    app.run()
