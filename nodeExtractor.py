import csv
import s2sphere


# Drawing a rectangle which contains the district of Zurich
southWest = s2sphere.LatLng.from_degrees(47.320203, 8.448083)
northEast = s2sphere.LatLng.from_degrees(47.434676, 8.625388)
rectangleZurichDistrict = s2sphere.LatLngRect.from_point_pair(southWest, northEast)


class PacketTransmission:

	def __init__(self, trans_id, time, lat, lon):
		self.trans_id = trans_id
		self.time = time
		self.lat = lat
		self.lon = lon


# Initializing the dictionary, which will hold all Transmission-objects per key (= nodeaddr)
packetDict = {}

# Initializing the dictionary of keys (nodeaddr) of outlying end devices
outlierDict = {}

# Parsing the .csv-file
# TODO: change file to actual DB dump
with open('test.csv', 'r', encoding='unicode_escape') as csv_file:
	csv_reader = csv.reader(csv_file)

	# skipping the first line (fieldnames)
	next(csv_file)

	for line in csv_reader:
		outlying = False
		# if for a given key (nodeaddr) no Transmission list exists yet, initialize an empty list at the key (line[2])
		if not (line[2] in packetDict):
			# checking, if some point lies on the defined rectangle
			tempPoint = s2sphere.LatLng.from_degrees(float(line[10]), float(line[11]))
			if rectangleZurichDistrict.contains(tempPoint):
				packetDict[line[2]] = []
			else:
				outlying = True
		if not outlying:
			packetDict.get(line[2]).append(PacketTransmission(line[0], line[1], line[10], line[11]))

# printing all keys (nodeaddr)
for i in packetDict:
	print("key \"" + i + "\", number of packets: " + str(len(packetDict[i])))
