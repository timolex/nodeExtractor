import json
import s2sphere as s2
import pyproj as proj
import math

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

northWestX, northWestY = (0.5 * radius), (1.5 * radius)
northEastX, northEastY = (1.5 * radius), (1.5 * radius)
southWestX, southWestY = (0.5 * radius), (0.5 * radius)
southEastX, southEastY = (1.5 * radius), (0.5 * radius)

nwNearestX, nwNearestY, nwMinDistance = 0, 0, 100000
neNearestX, neNearestY, neMinDistance = 0, 0, 100000
swNearestX, swNearestY, swMinDistance = 0, 0, 100000
seNearestX, seNearestY, seMinDistance = 0, 0, 100000
cenNearestX, cenNearestY, cenMinDistance = 0, 0, 100000


with open('gwData.json', 'r') as data_file:
	data = json.load(data_file)
	for v in data.values():
		if 'location' in v:
			tempPoint = s2.LatLng.from_degrees(v['location']['latitude'], v['location']['longitude']).to_point()
			# checking, if the point is contained in the defined shape

			if region.contains(tempPoint):
				lon = v['location']['longitude']
				lat = v['location']['latitude']
				x, y = proj.transform(proj_WGS84, proj_CH1903, lon, lat)
				x, y = x - offsetX, y - offsetY

				tempNwDist = math.sqrt((x-northWestX)**2 + (y-northWestY)**2)
				tempNeDist = math.sqrt((x-northEastX)**2 + (y-northEastY)**2)
				tempSwDist = math.sqrt((x-southWestX)**2 + (y-southWestY)**2)
				tempSeDist = math.sqrt((x-southEastX)**2 + (y-southEastY)**2)
				tempCenDist = math.sqrt((x-radius)**2 + (y-radius)**2)

				if tempNwDist < nwMinDistance:
					nwMinDistance = tempNwDist
					nwNearestX = x
					nwNearestY = y

				if tempNeDist < neMinDistance:
					neMinDistance = tempNeDist
					neNearestX = x
					neNearestY = y

				if tempSwDist < swMinDistance:
					swMinDistance = tempSwDist
					swNearestX = x
					swNearestY = y

				if tempSeDist < seMinDistance:
					seMinDistance = tempSeDist
					seNearestX = x
					seNearestY = y

				if tempCenDist < cenMinDistance:
					cenMinDistance = tempCenDist
					cenNearestX = x
					cenNearestY = y

				# if 'description' in v:
				# 	print('GW description: ' + v['description'] + '; x: ' + str(x) + ', y: ' + str(y))
				# else:
				# 	print('GW description: [unknown description]: ' + '; x: ' + str(x) + ', y: ' + str(y))
				#print('  gatewayPositions.push_back(Vector (' + str(x) + ', ' + str(y) + ", 0.0));")

	print('  gatewayPositions.push_back(Vector (' + str(nwNearestX) + ', ' + str(nwNearestY) + ", 0.0));")
	print('  gatewayPositions.push_back(Vector (' + str(neNearestX) + ', ' + str(neNearestY) + ", 0.0));")
	print('  gatewayPositions.push_back(Vector (' + str(swNearestX) + ', ' + str(swNearestY) + ", 0.0));")
	print('  gatewayPositions.push_back(Vector (' + str(seNearestX) + ', ' + str(seNearestY) + ", 0.0));")
	print('  gatewayPositions.push_back(Vector (' + str(cenNearestX) + ', ' + str(cenNearestY) + ", 0.0));")

	print("\ndistances:")
	print('NW: ', nwMinDistance)
	print('NE: ', neMinDistance)
	print('SW: ', swMinDistance)
	print('SE: ', seMinDistance)
	print('CEN: ', cenMinDistance)
