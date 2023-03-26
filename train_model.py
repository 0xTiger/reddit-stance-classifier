from collections import defaultdict

import numpy as np
from sklearn.metrics import confusion_matrix, f1_score
from sentence_transformers import SentenceTransformer
import torch
import torch.nn.functional as F
from tqdm import tqdm


if __name__ == '__main__':
    from tables import Comment, Stance, db
    from collections import defaultdict

    comments = (
        Comment.query
        .with_entities(Comment.author, Comment.subreddit, Comment.body)
        .limit(1_000_000)
        .all()
    )
    stances = Stance.query.all()

    sentence_trans = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')
    sentence_embeddings = sentence_trans.encode([comment[-1] for comment in comments], show_progress_bar=True, batch_size=1024)

    stances_dict = dict()
    author_embeddings = defaultdict(list)
    for (author, subreddit, comment), embedding in zip(comments, sentence_embeddings):
        author_embeddings[author].append(embedding)
    for stance in stances:
        stances_dict[stance.name] = (stance.v_pos, stance.h_pos)

    features, labels = [], []
    for author, embeddings in author_embeddings.items():
        label = stances_dict.get(author)
        if label:
            features.append(sum(embeddings) / len(embeddings))
            labels.append(label)


    X = np.array(features)
    y = np.array(labels)
    not_centerist = y[:, 1] != 0
    X = X[not_centerist]
    y = (y[not_centerist, 1] > 0)[:, np.newaxis]
    X = torch.tensor(X, dtype=torch.float)
    y = torch.tensor(y, dtype=torch.float)

    num_instances = X.shape[0]
    train_mask = torch.tensor(np.arange(num_instances) <= num_instances * 90 // 100, dtype=torch.bool)
    test_mask = torch.tensor(np.arange(num_instances) > num_instances * 90 // 100, dtype=torch.bool)
    class LinearMLP(torch.nn.Module):
        def __init__(self):
            super(LinearMLP, self).__init__()
            self.linear1 = torch.nn.Linear(384, 64)
            self.linear3 = torch.nn.Linear(64, 1)
            self.norm = torch.nn.InstanceNorm1d(384)

        def forward(self, x):
            x = self.norm(x)
            x = self.linear1(x)
            x = self.linear3(x)
            return F.sigmoid(x)

    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    model = LinearMLP().to(device)
    X = X.to(device)
    y = y.to(device)
    optimizer = torch.optim.NAdam(model.parameters(), lr=0.00001, weight_decay=5e-4)

    model.train()
    pbar = tqdm(range(5000))
    for epoch in pbar:
        optimizer.zero_grad()
        out = model(X)
        loss = F.binary_cross_entropy(out[train_mask], y[train_mask])
        loss.backward()
        val_loss = F.binary_cross_entropy(out[test_mask], y[test_mask])
        pbar.set_description(f'val_loss: {val_loss:.3f}')
        optimizer.step()

    model.eval()
    pred = model(X)
    y_pred = pred[test_mask].cpu().detach().numpy()
    y_test = y[test_mask].cpu().detach().numpy()

    print(f1_score(y_test, y_pred > 0.5))
