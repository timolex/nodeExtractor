import matplotlib.pyplot as plt
from imageio import imread
import csv

x, y, gwX, gwY = [], [], [], []

with open('coordinatesEDs.csv') as csvFile:
	readCSV = csv.reader(csvFile, delimiter=',')
	# skipping the first row
	next(csvFile)

	for row in readCSV:
		x.append(float(row[0]))
		y.append(float(row[1]))

with open('coordinatesGWs.csv') as csvFile:
	readCSV = csv.reader(csvFile, delimiter=',')
	# skipping the first row
	next(csvFile)

	for row in readCSV:
		gwX.append(float(row[0]))
		gwY.append(float(row[1]))

img = imread('Zurich.png')

plt.figure(dpi=600)
plt.scatter(x, y, zorder=1, color='green')
plt.scatter(gwX, gwY, zorder=1, color='blue')
plt.imshow(img, zorder=0, extent=[0.0, 20000.0, 0.0, 20000.0])

plt.savefig("Zurich_TTN_nodes.png")
plt.show()
