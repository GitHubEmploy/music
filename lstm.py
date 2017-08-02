import tensorflow as tf
import glob
from tqdm import tqdm
import numpy as np
from midi_manipulation import midiToNoteStateMatrix
from midi_manipulation import noteStateMatrixToMidi

#np.set_printoptions(threshold=np.nan)

def split_list(l, n):
    list = []
    for j in range(0, len(l), n):
        if (j + n < len(l)):
            list.append(np.array(l[j:j + n]))

    return list

def get_songs(path):
    '''
    :param path: path to the songs directory
    :return: array of songs w/ timestamp events
    '''
    files = glob.glob('{}/*.mid*'.format(path))
    songs = []
    for f in tqdm(files):
        try:

            song = np.array(midiToNoteStateMatrix(f))
            songs.append(song)

        except Exception as e:
            raise e
    return songs

#Hyperparams
learning_rate = .5
#Batch Size
batch_size = 10
#Number of training
epochs = 10
#number of features
num_features = 156
#Layers in the hidden lstm layer
layer_units = 156
#Number of time steps to use
n_steps = 100
#Song directore
songs = get_songs('./beeth')

#process songs and take timestamp cuts
input_sequence = []
expected_output = []
seqlens = []
max_seqlen = max(map(len, songs))

for song in tqdm(songs):
    seqlens.append(len(song)-1)
    if (len(song) < max_seqlen):

        song = np.pad(song, pad_width=(((0, max_seqlen-len(song)), (0,0))), mode='constant', constant_values=0)

    input_sequence.append(song[0:len(song)-2])
    expected_output.append(song[1:len(song)-1])

num_songs = len(songs)
#Weights biases and placeholders
w = tf.Variable(tf.truncated_normal([layer_units, num_features], stddev=.1))
b = tf.Variable(tf.truncated_normal([num_features], stddev=.1))

#x is examples by time by features
x = tf.placeholder(tf.float32, (None, max_seqlen-2, num_features))
#y is examples by examples by features
y = tf.placeholder(tf.float32, (None, max_seqlen-2, num_features))
seqlen = tf.placeholder(tf.int32, (None))

def RNN(x, seqlen):
    '''
    :param x: rnn input data
    :param seqlen: array of sequence lengths in x
    :return: rnn last timestamp output
    '''

    lstm_cell = tf.contrib.rnn.BasicLSTMCell(layer_units)

    outputs, states = tf.nn.dynamic_rnn(lstm_cell, x, dtype=tf.float32, sequence_length=seqlen)

    ###do feed forward processing on note
    #split outputs into list
    outputs = tf.unstack(outputs, len(input_sequence))
    #loop through list to do operations on one
    for i in range(len(outputs)-1):
        #normal operations
        outputs[i] = tf.sigmoid(tf.matmul(outputs[i], w))+b

    #recombine list into tensor
    outputs = tf.stack(outputs)

    return outputs

pred = RNN(x, seqlen=seqlen)

# Cross entropy loss
cost = tf.losses.softmax_cross_entropy(y, logits=pred)
#Train with Adam Optimizer
optimizer = tf.train.RMSPropOptimizer(learning_rate=learning_rate).minimize(cost)

correct_pred = tf.equal(tf.round(pred), y)

init = tf.global_variables_initializer()

with tf.Session() as sess:
    sess.run(init)

    #train for epoch epochs
    for i in tqdm(range(epochs)):
        sess.run(optimizer, feed_dict={x: input_sequence, y: expected_output, seqlen: seqlens})
        print(sess.run(cost, feed_dict={x: input_sequence, y: expected_output, seqlen: seqlens}))


