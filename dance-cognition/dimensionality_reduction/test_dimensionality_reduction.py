import numpy as np
import matplotlib.pyplot as plt
import random
from pca import *
import argparse

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

pca = KernelPCA(n_components=2, args=args)
pca.fit(training_data)

training_data = np.array(training_data)
output_data = pca.inverse_transform(pca.transform(training_data))

plot_data = np.append(training_data, output_data, axis=0)
plot_colors = np.append(training_colors, output_colors, axis=0)

plt.scatter(plot_data[:,0], plot_data[:,1], c=plot_colors, alpha=0.3)
plt.show()
