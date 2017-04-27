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

batch = []
colors = []
for j in range(1000):
    if (random.random() > 0.5):
        vec = c1
        color = "red"
    else:
        vec = c2
        color = "green"
    batch.append(np.random.normal(vec, 0.1))
    colors.append(color)

pca = KernelPCA(n_components=2, args=args)
pca.fit(batch)

batch = np.array(batch)
output = pca.inverse_transform(pca.transform(batch))

while True:
    plt.clf()
    plt.scatter(batch[:,0], batch[:,1], c=colors)
    plt.show(False)
    plt.pause(0.5)

    plt.clf()
    plt.scatter(output[:,0], output[:,1], c=colors)
    plt.show(False)
    plt.pause(0.5)
