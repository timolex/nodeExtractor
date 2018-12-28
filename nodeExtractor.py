import csv
import s2sphere  # https://s2sphere.readthedocs.io/en/latest/index.html
import math
import datetime
import numpy
import matplotlib.pyplot as plot
import time
import pyproj as proj

# 'program parameters:'
TESTING_MODE = False
MINIMUM_PEAK_TO_TRANSMISSIONS_RATIO = 0.5
# this value has to be at least 2 for fft to work properly
MINIMUM_NO_OF_PACKETS_SENT = 100
# criterion for filtering out short-living nodes
# This value must be in between the periodicity boundaries used for Mostafa's method
# MINIMUM_LIFESPAN = 2592000 # 30 days in seconds
# MINIMUM_LIFESPAN = 86400  # 24h in seconds
MINIMUM_LIFESPAN = 8000  # for testing
# periodicity boundaries used for the frequency cutoff in Mostafa's method
UPPER_BOUND_PERIODICITY = 7200  # 2h in seconds
LOWER_BOUND_PERIODICITY = 1209600  # 2 weeks in seconds

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
	filename = "1M.csv"

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

keptNodesLifespanCheck = {}
shortLivingNodes = {}
keptNodesMethodTimo = {}
remainderMethodTimo = {}
keptNodesMethodMostafa = {}
remainderMethodMostafa = {}
keptNodesMethodMachineLearning = {}
remainderMethodMachineLearning = {}

# filtering out short-living nodes, resp. nodes with too little transmissions
for node in nodeDict:
	# calculating the time-difference between first and last transmission in seconds
	timeSpan = nodeDict[node].__getitem__(len(nodeDict[node]) - 1).time_stamp - nodeDict[node].__getitem__(0).time_stamp
	packetLength = len(nodeDict[node])

	if packetLength < MINIMUM_NO_OF_PACKETS_SENT:
		shortLivingNodes[node] = nodeDict[node]
		print('Failing lifespan check: ' + node + ' (reason: too little transmissions: '
								+ str(packetLength) + ' packets transmitted)')
	elif timeSpan < MINIMUM_LIFESPAN:
		shortLivingNodes[node] = nodeDict[node]
		print('Failing lifespan check: ' + node + ' (reason: lifespan between 1st and last transmission too short: '
								+ str(timeSpan) + ' s)')
	else:
		keptNodesLifespanCheck[node] = nodeDict[node]

# filtering after Timo's method (sine period between transmissions, determine strong single frequencies)
for node in keptNodesLifespanCheck:
	# building the sine list
	sinePeriodicity = []
	for i in range(len(keptNodesLifespanCheck[node]) - 1):
		# determining the next interval (time in seconds between two transmissions)
		j = i + 1
		interval = int(
			keptNodesLifespanCheck[node].__getitem__(j).__getattribute__('time_stamp')
			- keptNodesLifespanCheck[node].__getitem__(i).__getattribute__("time_stamp"))
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
		remainderMethodTimo[node] = keptNodesLifespanCheck[node]
		print('Failing Timo\'s method: ' + node + ' (reason: peak/transmissions-ratio too low: ' + str(ratio) + ')')
	else:
		keptNodesMethodTimo[node] = keptNodesLifespanCheck[node]
		# printing the peak periodicity (by converting the found peak frequency)
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
	timeSpan = remainderMethodTimo[node].__getitem__(len(remainderMethodTimo[node]) - 1).time_stamp \
					- remainderMethodTimo[node].__getitem__(0).time_stamp
	# initializing the counters
	secondCount = 0
	packetCount = 0
	startSecond = remainderMethodTimo[node].__getitem__(0).time_stamp
	# building the periodicityTable
	# initializing the periodicity table (list)
	periodicityTable = []
	while packetCount < len(remainderMethodTimo[node]) and secondCount <= timeSpan:
		if startSecond + secondCount == remainderMethodTimo[node].__getitem__(packetCount).time_stamp:
			# appending 1 to the periodicityTable to signalize a transmission at the current second
			periodicityTable.append(1)
			# skipping packetTransmissions in the same second
			while packetCount < len(remainderMethodTimo[node]) and \
					startSecond + secondCount == remainderMethodTimo[node].__getitem__(packetCount).time_stamp:
				packetCount = packetCount + 1
		else:
			# appending 0 to the periodicityTable if no transmission happened at current second
			periodicityTable.append(0)
		secondCount = secondCount + 1

	# computing fft for periodicityTable
	fftPeriodicityTable = numpy.abs(numpy.fft.rfft(periodicityTable))

	# converting the provided periodicity-cutoffs to the looked-at node's time domain
	if timeSpan < UPPER_BOUND_PERIODICITY:
		raise ValueError('Node\'s lifespan must strictly be greater than the lower bound periodicity!')
	else:
		upperBoundFrequency = int(round(timeSpan / UPPER_BOUND_PERIODICITY))
		if upperBoundFrequency > len(fftPeriodicityTable):
			upperBoundFrequency = len(fftPeriodicityTable-1)

	if timeSpan < LOWER_BOUND_PERIODICITY:
		lowerBoundFrequency = 1
	else:
		lowerBoundFrequency = int(round(timeSpan / LOWER_BOUND_PERIODICITY))

	# determining the peak frequency using the frequency-cutoff
	peakFrequencyY = 0
	peakFrequencyX = 0
	for i in range(lowerBoundFrequency, upperBoundFrequency):
		if fftPeriodicityTable[i] > peakFrequencyY:
			peakFrequencyY = fftPeriodicityTable[i]
			peakFrequencyX = i

	# converting the found peakFrequency to periodicity
	peakPeriodicity = int(round(timeSpan / peakFrequencyX))

	# checking back, if found peakPeriodicity appears frequently in periodicityTable
	intervalIndex = 0
	intervalCounter = 0
	intervalCountList = []
	for j in range(len(periodicityTable)):
		if periodicityTable[j] == 1:
			intervalCounter = intervalCounter + 1
		if intervalIndex == peakPeriodicity - 1:
			if intervalCounter != 0:
				intervalCountList.append(intervalCounter)
			intervalIndex = 0
			intervalCounter = 0
		intervalIndex = intervalIndex + 1

	# keep the node, if for at least 0.7% of the intervals (acc. to peakPeriodicity) there appeared transmissions
	if len(intervalCountList) > 0.7 * peakFrequencyX:
		print('Node ' + node + ' has been verified to be transmitting regularly all '
								+ str(peakPeriodicity) + ' seconds.')
		keptNodesMethodMostafa[node] = remainderMethodTimo[node]
	else:
		print('Failing Mostafa\'s method: ' + node + ' (reason: intervals/peakFrequency-ratio too low.')
		remainderMethodMostafa[node] = remainderMethodTimo[node]

# filtering after machine learning methods
# for node in remainderMethodMostafa: TODO: implementation


# printing the number of found end devices in the area
print("\n# of found suitable end devices in the defined area: " + str(len(keptNodesMethodTimo)
						+ len(keptNodesMethodMostafa) + len(keptNodesMethodMachineLearning)))

# printing nodes with regular traffic (after Timo's method)
print('')
for i in keptNodesMethodTimo:
	print("To be considered \"" + i + "\", number of packets: " + str(len(keptNodesMethodTimo[i])))

# printing nodes with regular traffic (after Mostafa's method)
print('')
for i in keptNodesMethodMostafa:
	print("To be considered \"" + i + "\", number of packets: " + str(len(keptNodesMethodMostafa[i])))


# setting up projections (according to Coordinate Reference Systems WGS84 (lat.-lon.) and CH1903 (Switzerland))
proj_WGS84 = proj.Proj(init='epsg:4326')
proj_CH1903 = proj.Proj(init='epsg:21781')  # http://epsg.io/21781

# iterating over keptNodesMethodTimo, converting coordinates to epsg:21781-projection
print('')
for node in keptNodesMethodTimo:
	lon = keptNodesMethodTimo[node].__getitem__(0).__getattribute__('lon')
	lat = keptNodesMethodTimo[node].__getitem__(0).__getattribute__('lat')
	x, y = proj.transform(proj_WGS84, proj_CH1903, lon, lat)
	print(node + ' x: ' + str(x) + ', y: ' + str(y))

for node in keptNodesMethodMostafa:
	lon = keptNodesMethodMostafa[node].__getitem__(0).__getattribute__('lon')
	lat = keptNodesMethodMostafa[node].__getitem__(0).__getattribute__('lat')
	x, y = proj.transform(proj_WGS84, proj_CH1903, lon, lat)
	print(node + ' x: ' + str(x) + ', y: ' + str(y))


# stopping the timer:
time_stop = time.clock()

# printing the execution time
print("\n\nexecution time: " + str(time_stop - time_start))
