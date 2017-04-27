import numpy as np
import matplotlib.pyplot as plt
import random

c1 = np.array([0.0, 0.5])
c2 = np.array([0.5, 0.0])

batch = []
colors = []
for j in range(100):
    # pick a random centroid
    if (random.random() > 0.5):
        vec = c1
        color = "red"
    else:
        vec = c2
        color = "green"
    batch.append(np.random.normal(vec, 0.1))
    colors.append(color)

batch = np.array(batch)
plt.scatter(batch[:,0], batch[:,1], c=colors)
plt.show()
