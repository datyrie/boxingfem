import matplotlib.pyplot as plt
import numpy as np

data = np.loadtxt("nodes.txt")

x = []
y = []
label = []

for d in data:
  x.append(d[1])
  y.append(d[2])
  label.append(str(d[0]))

plt.figure()
plt.scatter(x, y)
for i, l in enumerate(label):
  plt.text(x = x[i] + 0.3, y = y[i] + 0.3, s = l)
plt.show()
