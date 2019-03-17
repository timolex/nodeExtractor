import json
import s2sphere as s2
import pyproj as proj
import math
import matplotlib.pyplot as plt
from imageio import imread

EARTH_RADIUS = 6371000

# defining the center of the city of Zurich and the radius of the cap to be drawn around it
ZurichLon, ZurichLat = 8.54226, 47.37174
centerOfZurich = s2.LatLng.from_degrees(ZurichLat, ZurichLon)
radius = 10000

# setting up projections (according to Coordinate Reference Systems WGS84 (lat.-lon.) and CH1903 (Switzerland))
proj_WGS84 = proj.Proj(init='epsg:4326')
proj_CH1903 = proj.Proj(init='epsg:21781')  # http://epsg.io/21781

# converting the radius into the Angle format
angleRadius = s2.Angle.from_degrees(360 * radius / (2 * math.pi * EARTH_RADIUS))

# defining the cap
region = s2.Cap.from_axis_angle(centerOfZurich.to_point(), angleRadius)

# converting Zurich's WGS84-coordinates (EPSG 4326) to CH1903 (EPSG 21781)
ZurichX, ZurichY = proj.transform(proj_WGS84, proj_CH1903, ZurichLon, ZurichLat)

# calculating the offsets used for normalization of the cartesian coordinate system
offsetX, offsetY = ZurichX - radius, ZurichY - radius

# setting the locations of the 6 extracted regularly transmitting Zurich TTN nodes
node1X, node1Y = 9782.655684816418, 16407.83287118317
node2X, node2Y = 761.9884992111474, 12798.042369708477
node3X, node3Y = 6515.527137617231, 13605.91745874213
node4X, node4Y = 7930.596178661217, 11784.030245990027
node5X, node5Y = 9795.627437463845, 10606.133177199517
node6X, node6Y = 2547.116770894616, 6258.487048110168

node1NearestX, node1NearestY, node1MinDistance = 0, 0, 100000
node2NearestX, node2NearestY, node2MinDistance = 0, 0, 100000
node3NearestX, node3NearestY, node3MinDistance = 0, 0, 100000
node4NearestX, node4NearestY, node4MinDistance = 0, 0, 100000
node5NearestX, node5NearestY, node5MinDistance = 0, 0, 100000
node6NearestX, node6NearestY, node6MinDistance = 0, 0, 100000


with open('gwData.json', 'r') as data_file:
	data = json.load(data_file)
	for v in data.values():
		if 'location' in v:
			lon = v['location']['longitude']
			lat = v['location']['latitude']
			tempPoint = s2.LatLng.from_degrees(lat, lon).to_point()
			# checking, if the point is contained in the defined shape
			if region.contains(tempPoint):
				x, y = proj.transform(proj_WGS84, proj_CH1903, lon, lat)
				# normalizing the metric, cartesian coordinates
				x, y = x - offsetX, y - offsetY

				tempNode1Dist = math.sqrt((x-node1X)**2 + (y-node1Y)**2)
				tempNode2Dist = math.sqrt((x-node2X)**2 + (y-node2Y)**2)
				tempNode3Dist = math.sqrt((x-node3X)**2 + (y-node3Y)**2)
				tempNode4Dist = math.sqrt((x-node4X)**2 + (y-node4Y)**2)
				tempNode5Dist = math.sqrt((x-node5X)**2 + (y-node5Y)**2)
				tempNode6Dist = math.sqrt((x-node6X)**2 + (y-node6Y)**2)

				if tempNode1Dist < node1MinDistance:
					node1MinDistance = tempNode1Dist
					node1NearestX = x
					node1NearestY = y

				if tempNode2Dist < node2MinDistance:
					node2MinDistance = tempNode2Dist
					node2NearestX = x
					node2NearestY = y

				if tempNode3Dist < node3MinDistance:
					node3MinDistance = tempNode3Dist
					node3NearestX = x
					node3NearestY = y

				if tempNode4Dist < node4MinDistance:
					node4MinDistance = tempNode4Dist
					node4NearestX = x
					node4NearestY = y

				if tempNode5Dist < node5MinDistance:
					node5MinDistance = tempNode5Dist
					node5NearestX = x
					node5NearestY = y

				if tempNode6Dist < node6MinDistance:
					node6MinDistance = tempNode6Dist
					node6NearestX = x
					node6NearestY = y

				if 'description' in v:
					print('GW description: ' + v['description'] + '; x: ' + str(x) + ', y: ' + str(y))
				else:
					print('GW description: [unknown description]: ' + '; x: ' + str(x) + ', y: ' + str(y))

	print('  gatewayPositions.push_back(Vector (' + str(node1NearestX) + ', ' + str(node1NearestY) + ", 0.0));")
	print('  gatewayPositions.push_back(Vector (' + str(node2NearestX) + ', ' + str(node2NearestY) + ", 0.0));")
	print('  gatewayPositions.push_back(Vector (' + str(node3NearestX) + ', ' + str(node3NearestY) + ", 0.0));")
	print('  gatewayPositions.push_back(Vector (' + str(node4NearestX) + ', ' + str(node4NearestY) + ", 0.0));")
	print('  gatewayPositions.push_back(Vector (' + str(node5NearestX) + ', ' + str(node5NearestY) + ", 0.0));")
	print('  gatewayPositions.push_back(Vector (' + str(node6NearestX) + ', ' + str(node6NearestY) + ", 0.0));")

	print("\ndistances:")
	print('node1: ', node1MinDistance)
	print('node2: ', node2MinDistance)
	print('node3: ', node3MinDistance)
	print('node4: ', node4MinDistance)
	print('node5: ', node5MinDistance)
	print('node6: ', node6MinDistance)

x, y, gwX, gwY = [], [], [], []

x.append(node1X / 1000)
y.append(node1Y / 1000)

x.append(node2X / 1000)
y.append(node2Y / 1000)

x.append(node3X / 1000)
y.append(node3Y / 1000)

x.append(node4X / 1000)
y.append(node4Y / 1000)

x.append(node5X / 1000)
y.append(node5Y / 1000)

x.append(node6X / 1000)
y.append(node6Y / 1000)

gwX.append(node1NearestX / 1000)
gwY.append(node1NearestY / 1000)

gwX.append(node2NearestX / 1000)
gwY.append(node2NearestY / 1000)

gwX.append(node3NearestX / 1000)
gwY.append(node3NearestY / 1000)

gwX.append(node4NearestX / 1000)
gwY.append(node4NearestY / 1000)

gwX.append(node5NearestX / 1000)
gwY.append(node5NearestY / 1000)

gwX.append(node6NearestX / 1000)
gwY.append(node6NearestY / 1000)


img = imread('Zurich.png')

plt.figure(dpi=400)
plt.xlabel('km')
plt.ylabel('km')
plt.scatter(x, y, zorder=2, color='darkred', s=50)
plt.scatter(gwX, gwY, zorder=0, color='blue', s=170)
plt.imshow(img, zorder=1, extent=[0.0, 20.0, 0.0, 20.0])

plt.savefig("Zurich_small_scenario.png")
plt.show()
