import csv
import s2sphere

# https://s2sphere.readthedocs.io/en/latest/index.html


# defining the south-west and north-east border edges of the rectangle, which contains the district of Zurich
# southWest = s2sphere.LatLng.from_degrees(47.320203, 8.448083)
# northEast = s2sphere.LatLng.from_degrees(47.434676, 8.625388)

# use these mock values to work with test.csv
southWest = s2sphere.LatLng.from_degrees(0, 0)
northEast = s2sphere.LatLng.from_degrees(90, 180)

rectangleZurichDistrict = s2sphere.LatLngRect.from_point_pair(southWest, northEast)


class PacketTransmission:

	def __init__(self, trans_id, time, lat, lon):
		self.trans_id = trans_id
		self.time = time
		self.lat = lat
		self.lon = lon


# Initializing the dictionary, which will hold all Transmission-objects per key (= nodeaddr)
packetDict = {}

# Parsing the .csv-file
# TODO: change file to actual DB dump
with open('test.csv', 'r', encoding='unicode_escape') as csv_file:
	csv_reader = csv.reader(csv_file)

	# skipping the first line (fieldnames)
	next(csv_file)

	for line in csv_reader:
		# building a temporary point at the lat./lon.-position of the looked-at packet transmission
		tempPoint = s2sphere.LatLng.from_degrees(float(line[10]), float(line[11]))
		# checking, if the point is contained in the defined rectangle
		if rectangleZurichDistrict.contains(tempPoint):
			# if for a given nodeaddr no key in packetDict exists yet, initialize an empty list at this key (line[2])
			if not (line[2] in packetDict):
				packetDict[line[2]] = []
			packetDict.get(line[2]).append(PacketTransmission(line[0], line[1], line[10], line[11]))

# printing all keys (nodeaddr)
for i in packetDict:
	print("key \"" + i + "\", number of packets: " + str(len(packetDict[i])))

# printing the number of found end devices in the area
print("\n# of found end devices in the defined area: " + str(len(packetDict)))
