import numpy as np
import matplotlib.pyplot as plt
import random
from pca import *
import argparse
import tensorflow as tf
import math

num_input_dimensions = 2
num_reduced_dimensions = 2
num_hidden_nodes = 3

def create(input_layer, layer_sizes):

	# Build the encoding layers
	next_layer_input = input_layer

	encoding_matrices = []
	for dim in layer_sizes:
		input_dim = int(next_layer_input.get_shape()[1])

		# Initialize W using random values in interval [-1/sqrt(n) , 1/sqrt(n)]
		W = tf.Variable(tf.random_uniform([input_dim, dim], -1.0 / math.sqrt(input_dim), 1.0 / math.sqrt(input_dim)))

		# Initialize b to zero
		b = tf.Variable(tf.zeros([dim]))

		# We are going to use tied-weights so store the W matrix for later reference.
		encoding_matrices.append(W)

		output = tf.nn.tanh(tf.matmul(next_layer_input,W) + b)

		# the input into the next layer is the output of this layer
		next_layer_input = output

	# The fully encoded x value is now stored in the next_layer_input
	encoded_x = next_layer_input

	# build the reconstruction layers by reversing the reductions
	layer_sizes.reverse()
	encoding_matrices.reverse()


	for i, dim in enumerate(layer_sizes[1:] + [ int(input_layer.get_shape()[1])]) :
		# we are using tied weights, so just lookup the encoding matrix for this step and transpose it
		W = tf.transpose(encoding_matrices[i])
		b = tf.Variable(tf.zeros([dim]))
		output = tf.nn.tanh(tf.matmul(next_layer_input,W) + b)
		next_layer_input = output

	# the fully encoded and reconstructed value of input_layer is here:
	reconstructed_input = next_layer_input

	return {
		'encoded': encoded_x,
		'decoded': reconstructed_input,
		'cost' : tf.sqrt(tf.reduce_mean(tf.square(input_layer-reconstructed_input)))
	}

sess = tf.Session()
input_layer = tf.placeholder("float", [None, num_input_dimensions])
autoencoder = create(input_layer, [num_hidden_nodes, num_reduced_dimensions])
init = tf.initialize_all_variables()
sess.run(init)
train_step = tf.train.GradientDescentOptimizer(0.05).minimize(autoencoder['cost'])


    
parser = argparse.ArgumentParser()
KernelPCA.add_parser_arguments(parser)
args = parser.parse_args()

c1 = np.array([0.1, 0.4])
c2 = np.array([0.4, 0.1])

training_data = []
training_colors = []
output_colors = []
for j in range(1000):
    if (random.random() > 0.5):
        vec = c1
        training_color = "#ff8080"
        output_color = "#ff0000"
    else:
        vec = c2
        training_color = "#80ff80"
        output_color = "#00ff00"
    training_data.append(np.random.normal(vec, 0.1))
    training_colors.append(training_color)
    output_colors.append(output_color)




pca = KernelPCA(n_components=num_reduced_dimensions, args=args)
pca.fit(training_data)

training_data = np.array(training_data)
# output_data = pca.inverse_transform(pca.transform(training_data))

# for i in range(5000):
#     sess.run(train_step, feed_dict={input_layer: training_data})
    
# output_data = sess.run(autoencoder['decoded'], feed_dict={input_layer: training_data})

# plot_data = np.append(training_data, output_data, axis=0)
# plot_colors = np.append(training_colors, output_colors, axis=0)

# plt.scatter(plot_data[:,0], plot_data[:,1], c=plot_colors, alpha=0.3)
# plt.show()

for i in range(1000):
    sess.run(train_step, feed_dict={input_layer: training_data})
    output_data = sess.run(autoencoder['decoded'], feed_dict={input_layer: training_data})

    plot_data = np.append(training_data, output_data, axis=0)
    plot_colors = np.append(training_colors, output_colors, axis=0)

    plt.clf()
    plt.scatter(plot_data[:,0], plot_data[:,1], c=plot_colors, alpha=0.3)
    plt.title('batch %d' % i)
    plt.show(False)
    plt.pause(0.0001)
