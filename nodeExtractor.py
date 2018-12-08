import csv
import s2sphere  # https://s2sphere.readthedocs.io/en/latest/index.html
import math
import datetime
import numpy

EARTH_RADIUS = 6371000

# mock values to work with test.csv
southWest = s2sphere.LatLng.from_degrees(0, 0)
northEast = s2sphere.LatLng.from_degrees(90, 180)

# defining a mock rectangle for testing
mockRegion = s2sphere.LatLngRect.from_point_pair(southWest, northEast)


# defining the center of the city of Zurich and the radius of the cap to be drawn around it
centerOfZurich = s2sphere.LatLng.from_degrees(47.37174, 8.54226)
radius = 5500

# converting the radius into the Angle format
angleRadius = s2sphere.Angle.from_degrees(360*radius/(2*math.pi*EARTH_RADIUS))

# defining the cap
capCoveringZurich = s2sphere.Cap.from_axis_angle(centerOfZurich.to_point(), angleRadius)


class PacketTransmission:

	def __init__(self, trans_id, time_stamp, lat, lon):
		self.trans_id = trans_id
		self.time_stamp = time_stamp
		self.lat = lat
		self.lon = lon


# initializing the dictionary, which will hold all Transmission-objects per key (= nodeaddr)
nodeDict = {}

# parsing the .csv-file
with open('test.csv', 'r', encoding='unicode_escape') as csv_file:
	csv_reader = csv.reader(csv_file)

	# skipping the first line (fieldnames)
	next(csv_file)

	for line in csv_reader:
		# building a temporary point at the lat./lon.-position of the looked-at packet transmission
		tempPoint = s2sphere.LatLng.from_degrees(float(line[10]), float(line[11])).to_point()
		# checking, if the point is contained in the defined shape
		if mockRegion.contains(tempPoint):
			# if for a given nodeaddr no key in nodeDict exists yet, initialize an empty list at this key (line[2])
			if not (line[2] in nodeDict):
				nodeDict[line[2]] = []
			timeStamp = datetime.datetime.strptime(line[1], '%Y-%m-%d %H:%M:%S').timestamp()
			nodeDict.get(line[2]).append(PacketTransmission(line[0], timeStamp, line[10], line[11]))

# filtering out non-periodically-sending nodes
nodesToRemove = []
for node in nodeDict:
	# calculating the time-difference between first and last transmission in seconds
	timeDiff = nodeDict[node].__getitem__(len(nodeDict[node]) - 1).time_stamp - nodeDict[node].__getitem__(0).time_stamp
	# initializing the periodicity table (list)
	periodicityTable = []
	# initializing the counters
	secondCount = 0
	packetCount = 0
	startSecond = nodeDict[node].__getitem__(0).time_stamp
	# building the table
	while packetCount < len(nodeDict[node]) and secondCount <= timeDiff:
		if startSecond + secondCount == nodeDict[node].__getitem__(packetCount).time_stamp:
			periodicityTable.append(1)
			packetCount = packetCount + 1
		else:
			periodicityTable.append(0)
		secondCount = secondCount + 1

	fftPeriodicityTable = numpy.abs(numpy.fft.rfft(periodicityTable))

	peakFound = False
	i = 1

	# TODO: Should there be a maximum for periodicities like implemented below?
	# filtering the nodes, while ignoring periodicities of greater than one week
	while peakFound is False and i < len(fftPeriodicityTable) and i < 606000:
		if fftPeriodicityTable[i] / fftPeriodicityTable[0] > 0.6:
			peakFound = True
		i = i+1

	# remove the node if no peak greater than 0.6*fft[0] was detected
	if not peakFound:
		# print the node to be filtered out
		print(node)
		nodesToRemove.append(node)

# removing all non-periodically-sending nodes from the nodeDict
for node in nodesToRemove:
	nodeDict.pop(node)

# printing all keys (nodeaddr)
for i in nodeDict:
	print("key \"" + i + "\", number of packets: " + str(len(nodeDict[i])))

# printing the number of found end devices in the area
print("\n# of found end devices in the defined area: " + str(len(nodeDict)))
