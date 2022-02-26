import numpy as np
from itertools import cycle
import matplotlib.pyplot as plt
from keras.models import Sequential
from keras.layers import LSTM, Dense, TimeDistributed
from keras.preprocessing.text import Tokenizer
from keras.callbacks import EarlyStopping
from tensorflow.python.keras.utils.np_utils import to_categorical
from tables import Comment, Stance


model = Sequential()
model.add(LSTM(32, return_sequences=True, input_shape=(None, 1)))
model.add(LSTM(8))
model.add(Dense(2, activation='sigmoid'))
# model.add(TimeDistributed(Dense(2, activation='sigmoid')))

print(model.summary(90))

model.compile(loss='categorical_crossentropy',
              optimizer='adam', metrics=['accuracy'])


comments = Comment.query.with_entities(Comment.body, Stance.h_pos).join(Stance, Comment.author == Stance.name).limit(5*10**6)
bodys, stances = [c[0] for c in comments if c[0] != 0], np.array([c[1:] for c in comments if c[0] != 0])

tokenizer = Tokenizer(num_words=None)
tokenizer.fit_on_texts(bodys)

sequences = tokenizer.texts_to_sequences(bodys)


split_idx = int(0.8*len(sequences))
train_sequences, test_sequences = sequences[:split_idx], sequences[split_idx:]
train_stances, test_stances = stances[:split_idx], stances[split_idx:]

def train_generator():
    for l in range(1, 100):
        X_train, y_train = [], []
        for seq, stance in zip(train_sequences, to_categorical(train_stances)):
            if len(seq) == l:
                X_train.append(seq)
                y_train.append(stance)
        if len(X_train) == 0:
            continue
        yield np.array(X_train)[:, :, np.newaxis], np.array(y_train)

def validation_generator():
    for l in range(1, 100):
        X_test, y_test = [], []
        for seq, stance in zip(test_sequences, to_categorical(test_stances)):
            if len(seq) == l:
                X_test.append(seq)
                y_test.append(stance)
        if len(X_test) == 0:
            continue
        yield np.array(X_test)[:, :, np.newaxis], np.array(y_test)

es = EarlyStopping(monitor='val_loss', mode='min', patience=2000, verbose=1)

history = model.fit(cycle(train_generator()), steps_per_epoch=100, epochs=5000, verbose=1, 
                    validation_data=cycle(validation_generator()), validation_steps=100, callbacks=[es])

fig1, ax1 = plt.subplots()
ax1.plot(history.history['loss'], label='Train Loss')
ax1.plot(history.history['val_loss'], label='Validation Loss')
ax1.plot(history.history['accuracy'], label='Train accuracy')
ax1.plot(history.history['val_accuracy'], label='Validation accuracy')
# ax1.axhline(baseline, color='k', ls='--', label='Naive Loss')
ax1.set_xlabel('epochs')
ax1.set_ylabel('loss')
ax1.legend()
plt.show()
pred = lambda comment: model.predict(np.array(tokenizer.texts_to_sequences([comment]))[:, :, np.newaxis])