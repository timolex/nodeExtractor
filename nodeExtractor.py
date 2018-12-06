import csv
import s2sphere  # https://s2sphere.readthedocs.io/en/latest/index.html
import math
import datetime

# defining the south-west and north-east border edges of the rectangle, which contains the district of Zurich
# southWest = s2sphere.LatLng.from_degrees(47.320203, 8.448083)
# northEast = s2sphere.LatLng.from_degrees(47.434676, 8.625388)

# use these mock values to work with test.csv
southWest = s2sphere.LatLng.from_degrees(0, 0)
northEast = s2sphere.LatLng.from_degrees(90, 180)

# defining the rectangle
rectangleZurichDistrict = s2sphere.LatLngRect.from_point_pair(southWest, northEast)

# defining the center of the city of Zurich and the radius of the cap to be drawn around it
center = s2sphere.LatLng.from_degrees(47.37174, 8.54226)
radius = 5500

EARTH_RADIUS = 6371000

# converting the radius into the Angle format
angleRadius = s2sphere.Angle.from_degrees(360*radius/(2*math.pi*EARTH_RADIUS))

# defining the cap
capCoveringZurich = s2sphere.Cap.from_axis_angle(center.to_point(), angleRadius)


class PacketTransmission:

	def __init__(self, trans_id, time, lat, lon):
		self.trans_id = trans_id
		self.time = time
		self.lat = lat
		self.lon = lon


# initializing the dictionary, which will hold all Transmission-objects per key (= nodeaddr)
packetDict = {}

# parsing the .csv-file
# for testing, use 'test.csv' as well as 'rectangleZurichDistrict' @ line 54
with open('test.csv', 'r', encoding='unicode_escape') as csv_file:
	csv_reader = csv.reader(csv_file)

	# skipping the first line (fieldnames)
	next(csv_file)

	for line in csv_reader:
		# building a temporary point at the lat./lon.-position of the looked-at packet transmission
		tempPoint = s2sphere.LatLng.from_degrees(float(line[10]), float(line[11])).to_point()
		# checking, if the point is contained in the defined shape
		# only use 'capAroundZurich' with actual .csv-dump, for testing, use 'rectangleZurichDistrict' and 'test.csv'
		if rectangleZurichDistrict.contains(tempPoint):
		# if capCoveringZurich.contains(tempPoint):
			# if for a given nodeaddr no key in packetDict exists yet, initialize an empty list at this key (line[2])
			if not (line[2] in packetDict):
				packetDict[line[2]] = []
			timeStamp = datetime.datetime.strptime(line[1], '%Y-%m-%d %H:%M:%S').timestamp()
			packetDict.get(line[2]).append(PacketTransmission(line[0], timeStamp, line[10], line[11]))

# printing all keys (nodeaddr)
for i in packetDict:
	print("key \"" + i + "\", number of packets: " + str(len(packetDict[i])))

# printing the number of found end devices in the area
print("\n# of found end devices in the defined area: " + str(len(packetDict)))

# node for testing: skylabmapper3
tempNode = packetDict.get("skylabmapper3")
# calculating the time-difference between first and last transmission in seconds
timeDiff = tempNode.__getitem__(len(tempNode) - 1).time - tempNode.__getitem__(0).time
# building the periodicity table (list)
periodicityTable = []
# initializing the counters
secondCount = 0
packetCount = 0
startSecond = tempNode.__getitem__(0).time
# building the table
while packetCount < len(tempNode) and secondCount <= timeDiff:
	if startSecond + secondCount == tempNode.__getitem__(packetCount).time:
		periodicityTable.append(1)
		packetCount = packetCount + 1
	else:
		periodicityTable.append(0)
	secondCount = secondCount + 1
print(periodicityTable)
