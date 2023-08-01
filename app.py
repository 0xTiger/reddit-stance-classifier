import os
from typing import Union
from collections import defaultdict
from datetime import datetime, timedelta
from itertools import groupby
from http import HTTPStatus
import hashlib

import httpagentparser
from requests.exceptions import HTTPError
from flask import render_template, request, redirect, url_for, session, jsonify
from sqlalchemy import func
import stripe

from prediction import pred_lean
from utils import (
    stance_name_from_tuple,
    nested_list_to_table_html,
    stancemap,
    stancecolormap,
    ApiHandler,
)
from tables import User, Comment, Traffic
from connections import db, app


def get_real_ip(r) -> str:
    return (r.environ['HTTP_X_FORWARDED_FOR'] 
        if r.environ.get('HTTP_X_FORWARDED_FOR') is not None
        else r.environ['REMOTE_ADDR'])


def create_new_session(time: datetime, remote_addr: Union[str, None]):
    seed = f'{time}{remote_addr}'
    session['user'] = hashlib.md5(seed.encode('utf-8')).hexdigest()

def get_analytics_data():
    userInfo = httpagentparser.detect(request.headers.get('User-Agent'), fill_none=True)
    time = datetime.now()
    if 'user' not in session:
        create_new_session(time, request.remote_addr)

    traffic = Traffic(
        ip=get_real_ip(request),
        os=userInfo['platform']['name'],
        browser=userInfo['browser']['name'],
        session_id=session['user'],
        path=request.path,
        method=request.method,
        timestamp=time,
    )
    db.session.add(traffic)
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
                handler = ApiHandler(session)
                user_data = handler.get_user_data(username)
                comments_data = handler.get_comment_data(username)
            except HTTPError as err:
                if err.response.status_code == HTTPStatus.NOT_FOUND:
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


def get_traffic_data(increment, value, sessions=False):
    since = datetime.now() - value * increment
    if sessions:
        traffics = (
            Traffic.query.with_entities(func.min(Traffic.timestamp))
            .where(Traffic.timestamp > since)
            .order_by(func.min(Traffic.timestamp))
            .group_by(Traffic.session_id)
            .all()
        )
        incremental_traffic = {
            'sessions': binned_counts(increment, value, (t[0] for t in traffics))
        }
    else:
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
    sessions = request.args.get('sessions', 'false').lower() == 'true'
    chart_type = request.args.get('chart_type', 'line')
    value, increment = int(since[:-1]), since[-1:]
    increment = {
        'w': timedelta(weeks=1),
        'd': timedelta(days=1),
        'h': timedelta(hours=1),
        'm': timedelta(minutes=1),
        's': timedelta(seconds=1),
    }.get(increment)
    

    traffic_frequency = get_traffic_data(increment, value, sessions)
    available_colors = ['grey', 'red', 'blue', 'green', 'yellow', 'orange']
    datasets = [
        {
            'label': path, 
            'data': traffics, 
            'fill': '-1' if i else 'origin', 
            'borderColor': available_colors[i % len(available_colors)], 
            'backgroundColor': available_colors[i % len(available_colors)],
            'pointHitRadius': 10,
            'pointRadius': 0,
        }
        for i, (path, traffics) in enumerate(traffic_frequency.items())
    ]
    return render_template("traffic.html",
        chart_type=chart_type,
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


@app.route("/stripe-key")
def get_publishable_key():
    stripe_config = {"publicKey": os.getenv('STRIPE_PUBLISHABLE_KEY')}
    return jsonify(stripe_config)


@app.route("/create-checkout-session")
def create_checkout_session():
    stripe.api_key = os.getenv('STRIPE_SECRET_KEY')
    # For full details see https://stripe.com/docs/api/checkout/sessions/create
    # ?session_id={CHECKOUT_SESSION_ID} means the redirect will have the session ID set as a query param
    try:
        checkout_session = stripe.checkout.Session.create(
            success_url=app.config['DOMAIN_URL'] + 'donation-success?session_id={CHECKOUT_SESSION_ID}',
            cancel_url=app.config['DOMAIN_URL'] + 'donation-cancelled',
            payment_method_types=['card'],
            mode='payment',
            line_items=[
                {
                    'price': os.getenv('DONATION_PRICE_ID'),
                    'quantity': 1,
                }
            ]
        )
        return jsonify({'sessionId': checkout_session['id']})
    except Exception as e:
        print(e)
        return jsonify(error=str(e)), 403


@app.route("/donation-success")
def donation_success():
    donation_banner = """
    <div style="background: rgba(52, 235, 82, 80); width: 100%;">
        <p style="color: darkgreen; text-align: center;">Donation Success, Thank you!</p>
    </div>
    """
    return render_template("about.html", donation_banner=donation_banner)


@app.route("/donation-cancelled")
def donation_cancelled():
    donation_banner = """
    <div style="background: rgba(235, 64, 52, 80); width: 100%;">
        <p style="color: darkred; text-align: center;">Donation Cancelled</p>
    </div>
    """
    return render_template("about.html", donation_banner=donation_banner)


if __name__ == '__main__':
    app.run(host='0.0.0.0')
