#!/usr/bin/env python
# https://github.com/sunnynevarekar/Fashion-MNIST/blob/master/Fashion-MNIST.ipynb

import numpy as np
import tensorflow as tf
from dataset import fashion_MNIST_CNN
from util import config
from progressbar import ProgressBar
from msvag import MSVAGOptimizer

def model(batch_x):

    """
    We will define the learned variables, the weights and biases,
    within the method ``model()`` which also constructs the neural network.
    The variables named ``hn``, where ``n`` is an integer, hold the learned weight variables.
    The variables named ``bn``, where ``n`` is an integer, hold the learned bias variables.
    In particular, the first variable ``h1`` holds the learned weight matrix that
    converts an input vector of dimension ``n_input + 2*n_input*n_context``
    to a vector of dimension ``n_hidden_1``.
    Similarly, the second variable ``h2`` holds the weight matrix converting
    an input vector of dimension ``n_hidden_1`` to one of dimension ``n_hidden_2``.
    The variables ``h3``, ``h5``, and ``h6`` are similar.
    Likewise, the biases, ``b1``, ``b2``..., hold the biases for the various layers.

    The model consists of fully connected 2 hidden layers along with input and output layers.
    """
    layers = {}

    conv1 = tf.layers.conv2d(inputs=batch_x, filters=32, kernel_size=[5,5], padding="same", activation=tf.nn.relu)
    pool1 = tf.layers.max_pooling2d(inputs=conv1, pool_size=[2,2], strides=2)

    conv2 = tf.layers.conv2d(inputs=pool1, filters=64, kernel_size=[5,5], padding="same", activation=tf.nn.relu)
    pool2 = tf.layers.max_pooling2d(inputs=conv2, pool_size=[2, 2], strides=2)

    pool2_flat = tf.reshape(pool2, shape=[-1, 7*7*64])

    #dense layer
    dense = tf.layers.dense(
        inputs=pool2_flat, 
        units=1024,
        activation=tf.nn.relu)
    
    #logits layer
    logits = tf.layers.dense(inputs=dense, units=10)
    
    return logits


def compute_loss(predicted, actual):
    """
    This routine computes the cross entropy log loss for each of output node/classes.
    returns mean loss is computed over n_class nodes.
    """

    total_loss = tf.nn.softmax_cross_entropy_with_logits_v2(logits = predicted,labels = actual)
    avg_loss = tf.reduce_mean(total_loss)
    return avg_loss


def create_optimizer():
    """
    we will use the Adam method for optimization (http://arxiv.org/abs/1412.6980),
    because, generally, it requires less fine-tuning.
    """

    optimizer = tf.train.AdamOptimizer(learning_rate=config.learning_rate)
    # optimizer = tf.train.GradientDescentOptimizer(learning_rate=config.learning_rate)
    # optimizer = MSVAGOptimizer(learning_rate=config.learning_rate, beta=0.9)
    return optimizer


def one_hot(n_class, Y):
    """
    returns one hot encoded labels to train output layers of NN model
    """
    return np.eye(n_class)[Y]

def fetch_batch(X_train, y_train, batch_index):
    """
    returns current batch to be executed
    """
    batch_X = X_train[(batch_index*config.batch_size):((batch_index+1)*config.batch_size),:]
    batch_y = y_train[(batch_index*config.batch_size):((batch_index+1)*config.batch_size),:]

    return batch_X, batch_y

def train(X_train, X_val, y_train, y_val, X_test, y_test, verbose = False):
    """
    Trains the network, also evaluates on test data finally.
    """

    # Creating place holders for image data and its labels
    tf.disable_eager_execution()
    X = tf.placeholder(tf.float32, [None, 28, 28, 1], name="X")
    Y = tf.placeholder(tf.float32, [None, 10], name="Y")

    # Forward pass on the model
    logits = model(X)

    # computing sofmax cross entropy loss with logits
    avg_loss = compute_loss(logits, Y)

    # create adams' optimizer, compute the gradients and apply gradients (minimize())
    optimizer = create_optimizer().minimize(avg_loss)

    # compute validation loss
    validation_loss = compute_loss(logits, Y)

    # evaluating accuracy on various data (train, val, test) set
    correct_prediction = tf.equal(tf.argmax(logits,1), tf.argmax(Y,1))
    accuracy = tf.reduce_mean(tf.cast(correct_prediction, "float"))

    # initialize all the global variables
    init = tf.global_variables_initializer()

    saver = tf.train.Saver()

    # starting session to actually execute the computation graph
    with tf.Session() as sess:

        # all the global varibles holds actual values now
        sess.run(init)
        train_accuracy_list = []
        train_loss_list = []
        val_accuracy_list = []
        val_loss_list = []

        # looping over number of epochs
        for epoch in range(config.n_epoch):

            if epoch % 10 == 0:
                save_path = saver.save(sess,"checkpoints/model_fmnist.ckpt")

            epoch_loss = 0.

            # calculate number of batches in dataset
            num_batches = np.round(X_train.shape[0]/config.batch_size).astype(int)

            # For displaying progresbar
            pbar = ProgressBar(term_width=80)

            # looping over batches of dataset
            for i in pbar(range(num_batches)):

                # selecting batch data
                batch_X, batch_y = fetch_batch(X_train, y_train, i)

                # execution of dataflow computational graph of nodes optimizer, avg_loss
                _, batch_loss = sess.run([optimizer, avg_loss],
                                                    feed_dict = {X: batch_X, Y:batch_y})

                # summed up batch loss for whole epoch
                epoch_loss += batch_loss

            # average epoch loss
            epoch_loss = epoch_loss/num_batches
            # compute train accuracy
            train_accuracy = sess.run(accuracy, feed_dict = {X: X_train[:X_val.shape[0]], Y: y_train[:X_val.shape[0]]})

            # compute validation loss
            val_loss = sess.run(validation_loss, feed_dict = {X: X_val ,Y: y_val})
            # compute validation accuracy
            val_accuracy = sess.run(accuracy, feed_dict = {X: X_val, Y: y_val})

            train_accuracy_list.append(round(float(train_accuracy),4))
            train_loss_list.append(round(epoch_loss,4))
            val_accuracy_list.append(round(float(val_accuracy),4))
            val_loss_list.append(round(float(val_loss),4))

            # display within an epoch (train_loss, train_accuracy, valid_loss, valid accuracy)
            if verbose:
                print("epoch:{epoch_num}, train_loss: {train_loss}, train_accuracy: {train_acc},"
                "val_loss: {valid_loss}, val_accuracy: {val_acc}".format(
                epoch_num = epoch,
                train_loss = round(epoch_loss,3),
                train_acc = round(float(train_accuracy),2),
                valid_loss = round(float(val_loss),3),
                val_acc = round(float(val_accuracy),2)
                ))

        save_path = saver.save(sess, "model/model_fmnist_final.ckpt")

        train_data = np.array([train_loss_list, train_accuracy_list, val_loss_list, val_accuracy_list]).T

        np.savetxt("./data/ADAM_CNN.csv", train_data)

        sess.close()

def test(X_test, y_test):
    """
    Evaluates accuracy on the test set using stored trained tensorflow model
    """
    tf.reset_default_graph()
    saver = tf.train.import_meta_graph("model/model_fmnist_final.ckpt.meta")

    with tf.Session() as sess:

        saver.restore(sess, tf.train.latest_checkpoint("model"))

        # How to know all the tensor variables stored in the session ?
        '''
        from tensorflow.python.tools.inspect_checkpoint import print_tensors_in_checkpoint_file
        latest_ckp = tf.train.latest_checkpoint('model')
        print_tensors_in_checkpoint_file(latest_ckp, all_tensors=True, tensor_name='')       
        '''
        
        graph = tf.get_default_graph()
        h1 = graph.get_tensor_by_name("h1:0")
        b1 = graph.get_tensor_by_name("b1:0")
        h2 = graph.get_tensor_by_name("h2:0")
        b2 = graph.get_tensor_by_name("b2:0")
        h3 = graph.get_tensor_by_name("h3:0")
        b3 = graph.get_tensor_by_name("b3:0")

        # Creating place holders for image data and its labels
        print(h1.dtype)
        X = tf.placeholder(tf.float32, [None, 784], name="X")
        Y = tf.placeholder(tf.float32, [None, 10], name="Y")

        logits = tf.add(tf.matmul(tf.nn.relu(tf.add(tf.matmul(tf.nn.relu(tf.add(tf.matmul(X,h1),b1)),h2),b2)),h3),b3)

        # evaluating accuracy on various data (train, val, test) set
        correct_prediction = tf.equal(tf.argmax(logits,1), tf.argmax(Y,1))
        accuracy = tf.reduce_mean(tf.cast(correct_prediction, "float"))

        test_accuracy = sess.run(accuracy, feed_dict = {X: X_test, Y: y_test})
        print("Test Accuracy:",test_accuracy)
        sess.close()


def main(_):

    # Instantiating the dataset class
    fashion_mnist = fashion_MNIST_CNN.Dataset(data_download_path='./data/fashion', validation_flag=True, verbose=True)

    # Loading the fashion MNIST data
    X_train, X_val, X_test, Y_train, Y_val, Y_test = fashion_mnist.load_data()

    #Lets convert our training and testing data from pandas dataframes into numpy 
    #arrays needed to train our model

    X_train = X_train.reshape(X_train.shape[0], 28, 
                            28, 1)
    X_test = X_test.reshape(X_test.shape[0], 28, 28, 1)
    X_val = X_val.reshape(X_val.shape[0], 28, 28, 1)

    # Showing few exapmle images from dataset in 2D grid
    fashion_mnist.show_samples_in_grid(w=10,h=10)

    # One hot encoding of labels for output layer training
    y_train =  one_hot(config.n_class, Y_train)
    y_val = one_hot(config.n_class, Y_val)
    y_test = one_hot(config.n_class, Y_test)

    # Let's train and evaluate the fully connected NN model
    train(X_train, X_val, y_train, y_val, X_test, Y_test, True)
    # test(X_test, y_test)


if __name__ == '__main__' :
    tf.app.run(main)