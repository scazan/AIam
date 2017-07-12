from dimensionality_reduction import DimensionalityReduction
import numpy as np
import tensorflow as tf
import math
import random
from backports import tempfile
from zipfile import ZipFile
import os

class AutoEncoder(DimensionalityReduction):
    @staticmethod
    def add_parser_arguments(parser):
        parser.add_argument("--learning-rate", type=float, default=0.1)
        parser.add_argument("--num-hidden-nodes", type=int, default=3)
        parser.add_argument("--num-training-epochs", type=int, default=1000)

    def __init__(self, num_input_dimensions, num_reduced_dimensions, args):
        DimensionalityReduction.__init__(self, num_input_dimensions, num_reduced_dimensions, args)
        self._graph = tf.Graph()
        with self._graph.as_default():
            self._sess = tf.Session()
            self._create_layers(self.num_input_dimensions)
            self._saver = tf.train.Saver()
            self._set_up_logging()
            init = tf.initialize_all_variables()
            self._sess.run(init)
        self.set_learning_rate(args.learning_rate)

    def _set_up_logging(self):
        with tf.name_scope("summaries"):
            tf.summary.scalar("cost", self._cost)
        self._merged = tf.summary.merge_all()
        self._train_writer = tf.summary.FileWriter("logs/train", self._sess.graph)

    def set_learning_rate(self, learning_rate):
        with self._graph.as_default():
            self._train_step = tf.train.GradientDescentOptimizer(learning_rate).minimize(self._cost)

    def batch_train(self, training_data, num_training_epochs):
        with self._graph.as_default():
            try:
                for i in range(num_training_epochs):
                    summary, _ = self._sess.run(
                        [self._merged, self._train_step], feed_dict={self._input_layer: training_data})
                    self._train_writer.add_summary(summary, i)
            except KeyboardInterrupt:
                print "Training stopped at epoch %d" % i

    def train(self, training_data, return_loss=False):
        with self._graph.as_default():
            if return_loss:
                loss, _ = self._sess.run(
                    [self._cost, self._train_step], feed_dict={self._input_layer: training_data})
                return loss
            else:
                self._sess.run(self._train_step, feed_dict={self._input_layer: training_data})
                
    def _create_layers(self, num_input_dimensions):
        self._input_layer = tf.placeholder("float", [None, num_input_dimensions])
        # Build the encoding layers
        next_layer_input = self._input_layer

        self._encoding_matrices = []
        if self.args.num_hidden_nodes > 0:
            self._layer_sizes = [self.args.num_hidden_nodes, self.num_reduced_dimensions]
        else:
            self._layer_sizes = [self.num_reduced_dimensions]
        for dim in self._layer_sizes:
            input_dim = int(next_layer_input.get_shape()[1])

            # Initialize W using random values in interval [-1/sqrt(n) , 1/sqrt(n)]
            W = tf.Variable(tf.random_uniform([input_dim, dim], -1.0 / math.sqrt(input_dim), 1.0 / math.sqrt(input_dim)))

            # Initialize b to zero
            b = tf.Variable(tf.zeros([dim]))

            # We are going to use tied-weights so store the W matrix for later reference.
            self._encoding_matrices.append(W)

            output = tf.matmul(next_layer_input,W) + b

            # the input into the next layer is the output of this layer
            next_layer_input = output

        # The fully encoded x value is now stored in the next_layer_input
        self._encoded_x = next_layer_input

        # build the reconstruction layers by reversing the reductions
        self._layer_sizes.reverse()
        self._encoding_matrices.reverse()

        for i, dim in enumerate(self._layer_sizes[1:] + [ int(self._input_layer.get_shape()[1])]) :
            # we are using tied weights, so just lookup the encoding matrix for this step and transpose it
            W = tf.transpose(self._encoding_matrices[i])
            b = tf.Variable(tf.zeros([dim]))
            output = tf.nn.tanh(tf.matmul(next_layer_input,W) + b)
            next_layer_input = output

        # the fully encoded and reconstructed value of input_layer is here:
        self._reconstructed_input = next_layer_input

        self._cost = tf.sqrt(tf.reduce_mean(tf.square(self._input_layer-self._reconstructed_input)))
        
    def transform(self, observations):
        with self._graph.as_default():
            return self._sess.run(self._encoded_x, feed_dict={self._input_layer: observations})

    def inverse_transform(self, reductions):
        with self._graph.as_default():
            return self._sess.run(self._reconstructed_input, feed_dict={self._encoded_x: reductions})
    
    def save_model(self, path):
        with self._graph.as_default():
            with tempfile.TemporaryDirectory() as tempdir:
                self._saver.save(self._sess, "%s/model" % tempdir)
                with ZipFile(path, "w") as zipfile:
                    for root, dirs, files in os.walk(tempdir):
                        for filename in files:
                            zipfile.write(os.path.join(root, filename), filename)
        
    def load_model(self, path):
        with self._graph.as_default():
            with tempfile.TemporaryDirectory() as tempdir:
                zipfile = ZipFile(path, "r")
                zipfile.extractall(tempdir)
                self._saver.restore(self._sess, "%s/model" % tempdir)

    def supports_incremental_learning(self):
        return True
    
    def add_noise(self, amount):
        if len(self._layer_sizes) > 1:
            raise Exception("AutoEncoder.add_noise only supports single-layer networks")

        with self._graph.as_default():
            W = self._encoding_matrices[0]
            input_dim = int(self._input_layer.get_shape()[1])
            dim = self._layer_sizes[0]
            op = W.assign_add(tf.random_uniform([input_dim, dim], -amount, amount), use_locking=True)
            self._sess.run(op)
