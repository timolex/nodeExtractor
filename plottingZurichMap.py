import matplotlib.pyplot as plt
from imageio import imread
import csv

x, y, gwX, gwY = [], [], [], []

with open('coordinatesEDs.csv') as csvFile:
	readCSV = csv.reader(csvFile, delimiter=',')
	# skipping the first row
	next(csvFile)

	for row in readCSV:
		x.append(float(row[0]) / 1000)
		y.append(float(row[1]) / 1000)

with open('coordinatesGWs.csv') as csvFile:
	readCSV = csv.reader(csvFile, delimiter=',')
	# skipping the first row
	next(csvFile)

	for row in readCSV:
		gwX.append(float(row[0]) / 1000)
		gwY.append(float(row[1]) / 1000)

img = imread('Zurich.png')

plt.figure(dpi=400)
plt.xlabel('km')
plt.ylabel('km')
plt.scatter(x, y, zorder=1, color='darkred', s=10)
plt.scatter(gwX, gwY, zorder=2, color='blue', s=20)
plt.imshow(img, zorder=0, extent=[0.0, 20.0, 0.0, 20.0])

plt.savefig("Zurich_TTN_nodes.png")
plt.show()
