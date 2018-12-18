import csv
import s2sphere  # https://s2sphere.readthedocs.io/en/latest/index.html
import math
import datetime
import numpy
import matplotlib.pyplot as plot
import time

# 'program parameters:'
TESTING_MODE = True
USE_PERIODICITY_TABLE = False
MINIMUM_PEAK_TO_TRANSMISSIONS_RATIO = 0.4
# this value has to be at least 2 for fft to work properly
MINIMUM_NO_OF_PACKETS_SENT = 5

EARTH_RADIUS = 6371000

if TESTING_MODE:
	# setting the filename
	filename = "test.csv"

	# mock values to work with test.csv
	southWest = s2sphere.LatLng.from_degrees(0, 0)
	northEast = s2sphere.LatLng.from_degrees(90, 180)

	# defining a mock rectangle for testing
	region = s2sphere.LatLngRect.from_point_pair(southWest, northEast)
else:
	# setting the filename
	filename = "packets.csv"

	# defining the center of the city of Zurich and the radius of the cap to be drawn around it
	centerOfZurich = s2sphere.LatLng.from_degrees(47.37174, 8.54226)
	radius = 5500

	# converting the radius into the Angle format
	angleRadius = s2sphere.Angle.from_degrees(360 * radius / (2 * math.pi * EARTH_RADIUS))

	# defining the cap
	region = s2sphere.Cap.from_axis_angle(centerOfZurich.to_point(), angleRadius)


class PacketTransmission:

	def __init__(self, trans_id, time_stamp, lat, lon):
		self.trans_id = trans_id
		self.time_stamp = time_stamp
		self.lat = lat
		self.lon = lon


# initializing the dictionary, which will hold all Transmission-objects per key (= nodeaddr)
nodeDict = {}

# starting the timer
time_start = time.clock()

# parsing the .csv-file
with open(filename, 'r', encoding='unicode_escape') as csv_file:
	csv_reader = csv.reader(csv_file)

	# skipping the first line (fieldnames)
	next(csv_file)

	for line in csv_reader:
		# building a temporary point at the lat./lon.-position of the looked-at packet transmission
		tempPoint = s2sphere.LatLng.from_degrees(float(line[10]), float(line[11])).to_point()
		# checking, if the point is contained in the defined shape
		if region.contains(tempPoint):
			# if for a given nodeaddr no key in nodeDict exists yet, initialize an empty list at this key (line[2])
			if not (line[2] in nodeDict):
				nodeDict[line[2]] = []
			timeStamp = datetime.datetime.strptime(line[1], '%Y-%m-%d %H:%M:%S').timestamp()
			nodeDict.get(line[2]).append(PacketTransmission(line[0], timeStamp, line[10], line[11]))

# filtering out non-periodically-sending nodes
nodesToRemove = []
for node in nodeDict:
	# filtering only nodes, which sent more than MINIMUM_NO_OF_PACKETS_SENT packets
	if len(nodeDict[node]) >= MINIMUM_NO_OF_PACKETS_SENT:
		# calculating the time-difference between first and last transmission in seconds
		timeDiff = nodeDict[node].__getitem__(len(nodeDict[node]) - 1).time_stamp - nodeDict[node].__getitem__(
			0).time_stamp

		# initializing the counters
		secondCount = 0
		packetCount = 0
		startSecond = nodeDict[node].__getitem__(0).time_stamp
		# building the periodicityTable
		if USE_PERIODICITY_TABLE:
			# initializing the periodicity table (list)
			periodicityTable = []
			while packetCount < len(nodeDict[node]) and secondCount <= timeDiff:
				if startSecond + secondCount == nodeDict[node].__getitem__(packetCount).time_stamp:
					# appending 1 to the periodicityTable to signalize a transmission at the current second
					periodicityTable.append(1)
					# skipping packetTransmissions in the same second
					while packetCount < len(nodeDict[node]) and \
						startSecond + secondCount == nodeDict[node].__getitem__(packetCount).time_stamp:
						packetCount = packetCount + 1
				else:
					# appending 0 to the periodicityTable if no transmission happened at current second
					periodicityTable.append(0)
				secondCount = secondCount + 1

		# initializing the sine version of periodicityTable
		sinePeriodicity = []
		# building the sinePeriodicityTable
		for i in range(len(nodeDict[node]) - 1):
			# determining the next interval (time in seconds between two transmissions)
			j = i + 1
			interval = int(
				nodeDict[node].__getitem__(j).__getattribute__('time_stamp') - nodeDict[node].__getitem__(
					i).__getattribute__("time_stamp"))
			# adding 0 for sin(0) per default
			sinePeriodicity.append(0)
			# appending the y-values for one cycle of a sine wave which spans the current interval
			for q in range(interval - 1):
				sinePeriodicity.append(numpy.sin(2 * numpy.pi * (q + 1) / (interval + 1)))

		# computing fft for periodicityTable
		if USE_PERIODICITY_TABLE:
			fftPeriodicityTable = numpy.abs(numpy.fft.rfft(periodicityTable))

		# computing fft for sinePeriodicity
		fftSinTable = numpy.abs(numpy.fft.rfft(sinePeriodicity))

		# adding nodes to the nodesToRemove list, for which fft does not show a clear peak
		# (e.g., their peak/transmissions-ratio is too low)
		ratio = max(fftSinTable) / (len(fftSinTable))
		if ratio < MINIMUM_PEAK_TO_TRANSMISSIONS_RATIO:
			print('To be removed: ' + node + ' (reason: peak/transmissions-ratio too low: ' + str(ratio) + ')')
			nodesToRemove.append(node)
		else:
			print(node + ' maximum peak at ' + str(len(sinePeriodicity) / numpy.argmax(fftSinTable)) + ' seconds')

		# plotting a good example of test.csv
		if TESTING_MODE and node == 'skylabmapper3':
			if USE_PERIODICITY_TABLE:
				plot.plot(periodicityTable)
				plot.title("periodicityTable")
				plot.xlabel("seconds (between first and last transmission of node)")
				plot.ylabel("1 = packet sent, 0 = no packet sent")
				plot.show()
			plot.plot(sinePeriodicity)
			plot.title("sine version of periodicityTable")
			plot.xlabel("seconds (between first and last transmission of node)")
			plot.ylabel("sine wave, one full period between two transmissions")
			plot.show()
			plot.plot(fftSinTable)
			plot.title("fft on sinePeriodicity")
			plot.xlabel("seconds (between first and last transmission of node)")
			plot.show()
			if USE_PERIODICITY_TABLE:
				plot.plot(fftPeriodicityTable)
				plot.title("fft on periodicityTable")
				plot.xlabel("seconds (between first and last transmission of node)")
				plot.show()

	# filtering out nodes, which sent less than MINIMUM_NO_OF_PACKETS_SENT
	else:
		print('To be removed: ' + node + ' (reason: too little transmissions)')
		nodesToRemove.append(node)

# removing all non-periodically-sending nodes from the nodeDict
for node in nodesToRemove:
	nodeDict.pop(node)

# stopping the timer:
time_stop = time.clock()

# printing all keys (nodeaddr)
print('')
for i in nodeDict:
	print("To be considered \"" + i + "\", number of packets: " + str(len(nodeDict[i])))

# printing the number of found end devices in the area
print("\n# of found suitable end devices in the defined area: " + str(len(nodeDict)))

# printing the execution time
print("\n\nexecution time: " + str(time_stop - time_start))
