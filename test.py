import numpy as np
import matplotlib.pyplot as pl

x = np.linspace(0, 10, 100)
y = np.sin(x)

fig = pl.figure(figsize=(8,5))
ax = pl.gca()
pl.axis('off')
pl.plot(x, y)
pl.xlim(0,10)
pl.ylim(-1,1)

pl.subplots_adjust(left=0, right=1, top=1, bottom=0)
pl.show()