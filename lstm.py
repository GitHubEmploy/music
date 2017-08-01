import tensorflow as tf
import glob
from tqdm import tqdm
import numpy as np
from midi_manipulation import midiToNoteStateMatrix


def split_list(l, n):

    list = []
    for j in range(0, len(l), n):
        if (j+n < len(l)):
            list.append(np.array(l[j:j+n]))
    return list

def get_songs(path):
    files = glob.glob('{}/*.mid*'.format(path))
    songs = []
    for f in tqdm(files):
        try:
            song = np.array(midiToNoteStateMatrix(f))
            if np.array(song).shape[0] > 50:
                songs.append(song)
        except Exception as e:
            raise e
    return songs

#Hyperparams
learning_rate = .05
#Number of training
epochs = 10
layer_units = 156
n_steps = 10
songs = get_songs('./beeth')
notes_in_dataset = songs

w = tf.Variable(tf.truncated_normal([layer_units, 156], stddev=.1))
b = tf.Variable(tf.truncated_normal([156], stddev=.1))
x = tf.placeholder(tf.float32, (None, 10, 156))
y = tf.placeholder(tf.float32, (None, 156))

def RNN(x, w, b):

    lstm_cell = tf.contrib.rnn.BasicLSTMCell(layer_units)

    outputs, states = tf.nn.dynamic_rnn(lstm_cell, x, dtype=tf.float32, time_major=True)
    return tf.sigmoid(tf.matmul(tf.transpose(outputs, perm=[1, 0, 2])[-1], w) + b)

pred = RNN(x, w, b)

cost = tf.reduce_mean(tf.nn.softmax_cross_entropy_with_logits(logits=pred, labels=y))
optimizer = tf.train.AdamOptimizer(learning_rate=learning_rate).minimize(cost)

correct_pred = tf.equal(tf.round(pred), y)

init = tf.global_variables_initializer()

with tf.Session() as sess:
    sess.run(init)
    step = 0

    for i in tqdm(range(epochs)):
        input_sequence = []
        expected_output = []
        for song in songs:
            for offset in range(len(song)-n_steps-1):

                input_sequence.append(song[offset:offset+n_steps])
                expected_output.append(song[offset+n_steps+1])

        sess.run(optimizer, feed_dict={x: input_sequence, y: expected_output})

    print(sess.run(cost,feed_dict={x: input_sequence, y: expected_output}))
