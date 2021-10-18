import joblib
from collections import Counter
from tables import User, Prediction

full_pipeline = joblib.load('models/ensemble.pkl')

def pred_lean(user: User) -> Prediction:
    subreddit_counts = Counter(comment.subreddit for comment in user.comments)
    total = sum(n for n in subreddit_counts.values())
    if total < 800 or total >= 1000 + 10:
        scale = 1
    elif 800 <= total < 950:
        scale = ((1200 - 800)/(950 - 800)*(total - 800) + 800)/total
    elif 950 <= total < 1000 + 10:
        scale = ((3500 - 1200)/(1000 - 950)*(total - 950) + 1200)/total
        
    subreddit_counts = {k: scale*v for k,v in subreddit_counts.items()}

    v_pos, h_pos = full_pipeline.predict([subreddit_counts])[0]
    return Prediction(name=user.name, v_pos=v_pos, h_pos=h_pos)


