import csv
import s2sphere  # https://s2sphere.readthedocs.io/en/latest/index.html
import math
import datetime
import numpy
import matplotlib.pyplot as plot
import time
import pyproj as proj

# 'program parameters:'
TESTING_MODE = True
MINIMUM_PEAK_TO_TRANSMISSIONS_RATIO = 0.4
# this value has to be at least 2 for fft to work properly
MINIMUM_NO_OF_PACKETS_SENT = 2
# criterion for filtering out short-living nodes
# MINIMUM_LIFESPAN = 2592000 # 30 days in seconds
# MINIMUM_LIFESPAN = 86400  # 24 h in seconds
MINIMUM_LIFESPAN = 200  # for testing

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

keptNodesLifespanCheck = []
shortLivingNodes = []
keptNodesMethodTimo = []
remainderMethodTimo = []
keptNodesMethodMostafa = []
remainderMethodMostafa = []
keptNodesMethodMachineLearning = []
remainderMethodMachineLearning = []

# filtering out short-living nodes, resp. nodes with too little transmissions
for node in nodeDict:
	# calculating the time-difference between first and last transmission in seconds
	timeDiff = nodeDict[node].__getitem__(len(nodeDict[node]) - 1).time_stamp - nodeDict[node].__getitem__(0).time_stamp
	packetLength = len(nodeDict[node])

	if packetLength < MINIMUM_NO_OF_PACKETS_SENT or timeDiff < MINIMUM_LIFESPAN:
		shortLivingNodes.append(node)
		print('Failing lifespan check: ' + node + ' (reason: lifespan between 1st and last transmission too short: '
								+ str(timeDiff) + ' s)')
	else:
		keptNodesLifespanCheck.append(node)

# filtering after Timo's method (sine period between transmissions, determine strong single frequencies)
for node in keptNodesLifespanCheck:
	# building the sine list
	sinePeriodicity = []
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

	# computing fft for sinePeriodicity
	fftSinTable = numpy.abs(numpy.fft.rfft(sinePeriodicity))

	# adding passing nodes to the remainderMethodTimo list, for which fft does not show a clear peak
	# (e.g., their peak/transmissions-ratio is too low)
	ratio = max(fftSinTable) / (len(fftSinTable))
	if ratio < MINIMUM_PEAK_TO_TRANSMISSIONS_RATIO:
		remainderMethodTimo.append(node)
		print('Failing Timo\'s method: ' + node + ' (reason: peak/transmissions-ratio too low: ' + str(ratio) + ')')
	else:
		# printing the peak periodicity (by converting the found peak frequency)
		keptNodesMethodTimo.append(node)
		print('Node ' + node + ' is most regularly transmitting all '
								+ str(len(sinePeriodicity) / numpy.argmax(fftSinTable)) + ' seconds.')

	if node == 'skylabmapper3':
		plot.plot(sinePeriodicity)
		plot.title("sine version of periodicityTable")
		plot.xlabel("seconds (between first and last transmission of node)")
		plot.ylabel("sine wave, one full period between two transmissions")
		plot.show()
		plot.plot(fftSinTable)
		plot.title("fft on sinePeriodicity")
		plot.xlabel("seconds (between first and last transmission of node)")
		plot.show()

# filtering after Mostafa's method
for node in remainderMethodTimo:
	timeDiff = nodeDict[node].__getitem__(len(nodeDict[node]) - 1).time_stamp - nodeDict[node].__getitem__(0).time_stamp
	# initializing the counters
	secondCount = 0
	packetCount = 0
	startSecond = nodeDict[node].__getitem__(0).time_stamp
	# building the periodicityTable
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

	# computing fft for periodicityTable
	fftPeriodicityTable = numpy.abs(numpy.fft.rfft(periodicityTable))

# filtering after machine learning methods
# for node in remainderMethodMostafa: TODO: implementation

# printing the number of found end devices in the area
print("\n# of found suitable end devices in the defined area: " + str(len(keptNodesMethodTimo)
						+ len(keptNodesMethodMostafa) + len(keptNodesMethodMachineLearning)))

# printing nodes with regular traffic (after Timo's method)
print('')
for i in keptNodesMethodTimo:
	print("To be considered \"" + i + "\", number of packets: " + str(len(nodeDict[i])))

# setting up projections (according to Coordinate Reference Systems WGS84 (lat.-lon.) and CH1903 (Switzerland))
proj_WGS84 = proj.Proj(init='epsg:4326')
proj_CH1903 = proj.Proj(init='epsg:21781')  # http://epsg.io/21781

# iterating over keptNodesMethodTimo, converting coordinates to epsg:21781-projection
print('')
for node in keptNodesMethodTimo:
	lon = nodeDict[node].__getitem__(0).__getattribute__('lon')
	lat = nodeDict[node].__getitem__(0).__getattribute__('lat')
	x, y = proj.transform(proj_WGS84, proj_CH1903, lon, lat)
	print(node + ' x: ' + str(x) + ', y: ' + str(y))

# stopping the timer:
time_stop = time.clock()

# printing the execution time
print("\n\nexecution time: " + str(time_stop - time_start))
