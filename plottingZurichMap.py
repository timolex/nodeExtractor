import matplotlib.pyplot as plt
from imageio import imread

x = [9782.655684816418, 761.9884992111474, 6515.527137617231, 7930.596178661217, 9795.627437463845, 2547.116770894616]
y = [16407.83287118317, 12798.042369708477, 13605.91745874213, 11784.030245990027, 10606.133177199517, 6258.487048110168]

img = imread('Zurich.png')

plt.figure(dpi=600)
plt.scatter(x, y, zorder=1)
plt.imshow(img, zorder=0, extent=[0.0, 20000.0, 0.0, 20000.0])

plt.savefig("Zurich_TTN_nodes.png")
plt.show()
