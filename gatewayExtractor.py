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
				# if 'description' in v:
				# 	print('GW description: ' + v['description'] + '; x: ' + str(x) + ', y: ' + str(y))
				# else:
				# 	print('GW description: [unknown description]: ' + '; x: ' + str(x) + ', y: ' + str(y))
				print('  gatewayPositions.push_back(Vector (' + str(x) + ', ' + str(y) + ", 0.0));")


