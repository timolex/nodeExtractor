import csv
import s2sphere  # https://s2sphere.readthedocs.io/en/latest/index.html
import math
import datetime
import numpy
import matplotlib.pyplot as plot

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
	if len(nodeDict[node]) > 5:
		# calculating the time-difference between first and last transmission in seconds
		timeDiff = nodeDict[node].__getitem__(len(nodeDict[node]) - 1).time_stamp - nodeDict[node].__getitem__(
			0).time_stamp
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
				# jumping over packetTransmissions in the same second
				while packetCount < len(nodeDict[node]) and \
						startSecond + secondCount == nodeDict[node].__getitem__(packetCount).time_stamp:
					packetCount = packetCount + 1
			else:
				periodicityTable.append(0)
			secondCount = secondCount + 1

		if len(periodicityTable) > 1:
			sinePeriodicity = []
			for i in range(len(nodeDict[node]) - 1):
				j = i + 1
				interval = int(
					nodeDict[node].__getitem__(j).__getattribute__('time_stamp') - nodeDict[node].__getitem__(
						i).__getattribute__("time_stamp"))
				sinePeriodicity.append(0)
				for q in range(interval - 1):
					sinePeriodicity.append(numpy.sin(2 * numpy.pi * (q + 1) / (interval + 1)))

			fftPeriodicityTable = numpy.abs(numpy.fft.rfft(periodicityTable))
			fftSinTable = numpy.abs(numpy.fft.rfft(sinePeriodicity))

			if node == '0x01010601':
				plot.plot(periodicityTable)
				plot.title("periodicityTable")
				plot.xlabel("seconds (between first and last transmission of node)")
				plot.ylabel("1 = packet sent, 0 = no packet sent")
				plot.show()
				plot.plot(sinePeriodicity)
				plot.title("sine version of periodicityTable")
				plot.xlabel("seconds (between first and last transmission of node)")
				plot.ylabel("sine wave, one full period between two transmissions")
				print('Max of fftSinTable:')
				print(max(fftSinTable))
				print('length of periodicityTable / 2:')
				print(len(periodicityTable) / 2)
				print('ratio max/len:')
				print(str(max(fftSinTable) / (len(periodicityTable) / 2)))
				plot.show()
				plot.plot(fftSinTable)
				plot.title("fft on sin")
				plot.xlabel("seconds (between first and last transmission of node)")
				plot.show()
				plot.plot(fftPeriodicityTable)
				plot.title("fft on periodicityTable")
				plot.xlabel("seconds (between first and last transmission of node)")
				plot.show()

			if not (max(fftSinTable) / (len(periodicityTable) / 2)) > 0.4:
				# print the node to be filtered out
				print(node)
				nodesToRemove.append(node)
	else:
		# print the node to be filtered out due to too little transmissions
		print(node)
		nodesToRemove.append(node)

	# peakFound = False
		# i = 1
		#
		# # TODO: Should there be a maximum for periodicities like implemented below?
		# # filtering the nodes, while ignoring periodicities of greater than one week
		# while peakFound is False and i < len(fftPeriodicityTable) and i < 606000:
		# 	if fftPeriodicityTable[i] / fftPeriodicityTable[0] > 0.6:
		# 		peakFound = True
		# 	i = i+1
		#
		# # remove the node if no peak greater than 0.6*fft[0] was detected
		# if not peakFound:
		# 	# print the node to be filtered out
		# 	print(node)
		# 	nodesToRemove.append(node)

# removing all non-periodically-sending nodes from the nodeDict
for node in nodesToRemove:
	nodeDict.pop(node)

# printing all keys (nodeaddr)
for i in nodeDict:
	print("key \"" + i + "\", number of packets: " + str(len(nodeDict[i])))

# printing the number of found end devices in the area
print("\n# of found end devices in the defined area: " + str(len(nodeDict)))
