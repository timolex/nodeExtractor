import csv
import s2sphere  # https://s2sphere.readthedocs.io/en/latest/index.html
import math
import datetime
import numpy
import matplotlib.pyplot as plot
import time
import pyproj as proj

print('NodeExtractor started...')

# general parameters

# minimum frequency-peak to number-of-transmissions rate used in Timo's (sine) method
MINIMUM_PEAK_TO_TRANSMISSIONS_RATIO = 0.5
# following value has to be at least 2 for fft to work properly
MINIMUM_NO_OF_PACKETS_SENT = 15
# criterion for filtering out short-living nodes
# This value must be greater than the upper bound periodicity used for Mostafa's (direct) method
MINIMUM_LIFESPAN = 86400  # 24h in seconds
# periodicity boundaries used for the frequency cutoff in Mostafa's method
UPPER_BOUND_PERIODICITY = 7200  # 2h in s
LOWER_BOUND_PERIODICITY = 1209600  # 2 weeks in s
# minimum percentage of intervals which have to be successfully checked back in Mostafa's method
MINIMUM_INTERVAL_PERCENTAGE = 0.99

EARTH_RADIUS = 6371000  # in m

# setting up projections (according to Coordinate Reference Systems WGS84 (lat.-lon.) and CH1903 (Switzerland))
proj_WGS84 = proj.Proj(init='epsg:4326')
proj_CH1903 = proj.Proj(init='epsg:21781')  # http://epsg.io/21781

# setting the filename
filename = "input.csv"

# defining the center of the city of Zurich and the radius of the cap to be drawn around it
ZurichLon, ZurichLat = 8.54226, 47.37174
centerOfZurich = s2sphere.LatLng.from_degrees(ZurichLat, ZurichLon)
radius = 10000

# converting the radius into the Angle format
angleRadius = s2sphere.Angle.from_degrees(360 * radius / (2 * math.pi * EARTH_RADIUS))

# defining the cap around Zurich
region = s2sphere.Cap.from_axis_angle(centerOfZurich.to_point(), angleRadius)

# converting Zurich's WGS84-coordinates (EPSG 4326) to CH1903 (EPSG 21781)
ZurichX, ZurichY = proj.transform(proj_WGS84, proj_CH1903, ZurichLon, ZurichLat)

# calculating the offsets used for normalization of the cartesian coordinate system
offsetX, offsetY = ZurichX - radius, ZurichY - radius


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

# building the statistical periodicity table & function
periodicityDistribution = []
for i in range(0, 334):
	periodicityDistribution.append(0)


def register_periodicity(p):
	if UPPER_BOUND_PERIODICITY <= p < LOWER_BOUND_PERIODICITY:
		index = (p-7200) // 3600
		periodicityDistribution[int(index)] += 1


# filtering after Timo's method (Sine method): sine period between transmissions, determine strong single frequencies)
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

	# adding passing nodes to the remainderMethodTimo list, for which FFT does not show a clear peak
	# (i.e., their peak/transmissions-ratio is too low)
	ratio = max(fftSinTable) / (len(fftSinTable))
	if ratio < MINIMUM_PEAK_TO_TRANSMISSIONS_RATIO:
		remainderMethodTimo[node] = keptNodesLifespanCheck[node]
		print('Failing sine method: ' + node + ' (reason: peak/transmissions-ratio too low: ' + str(ratio) + ')')
	else:
		keptNodesMethodTimo[node] = keptNodesLifespanCheck[node]
		# printing the peak periodicity (by converting the found peak frequency)
		singularPeriodicityPeak = len(sinePeriodicity) / numpy.argmax(fftSinTable)

		print('Node ' + node + ' is most regularly transmitting all '
								+ str(singularPeriodicityPeak) + ' seconds.')
		register_periodicity(singularPeriodicityPeak)


# filtering after Mostafa's method (Direct method)
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

	# computing FFT for periodicityTable
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
	intervalSecond = 0
	transmissionCounter = 0
	intervalCountList = []
	for j in range(len(periodicityTable)):
		if periodicityTable[j] == 1:
			transmissionCounter = transmissionCounter + 1
		# determining, if already a whole interval (according to peakPeriodicity) has been checked
		if intervalSecond == peakPeriodicity - 1:
			# only consider the interval, if at least one transmission appeared within it
			if transmissionCounter > 0:
				intervalCountList.append(transmissionCounter)
			# resetting both the (inter-) intervalSecond as well as the transmissionCounter
			intervalSecond = 0
			transmissionCounter = 0
		intervalSecond = intervalSecond + 1

	# keep the node, if at least the specified percentage of intervals were checked back positively for transmissions
	if len(intervalCountList) > MINIMUM_INTERVAL_PERCENTAGE * peakFrequencyX:
		print('Node ' + node + ' has been verified to be transmitting regularly all '
								+ str(peakPeriodicity) + ' seconds.')
		keptNodesMethodMostafa[node] = remainderMethodTimo[node]
		register_periodicity(peakPeriodicity)
	else:
		print('Failing direct method: ' + node + ' (reason: intervals/peakFrequency-ratio too low.')
		remainderMethodMostafa[node] = remainderMethodTimo[node]


# printing the number of found end devices in the area
print("\n# of found suitable end devices in the defined area: " + str(len(keptNodesMethodTimo)
						+ len(keptNodesMethodMostafa) + len(keptNodesMethodMachineLearning)))


print("Coordinates of determined nodes (in terms of CH1903 Coordinate Reference System):")

# iterating over keptNodesMethodTimo, converting coordinates to epsg:21781-projection
print('\nConsiderable nodes sending most frequently at one peak periodicity (Sine method):')
for node in keptNodesMethodTimo:
	lon = keptNodesMethodTimo[node].__getitem__(0).__getattribute__('lon')
	lat = keptNodesMethodTimo[node].__getitem__(0).__getattribute__('lat')
	x, y = proj.transform(proj_WGS84, proj_CH1903, lon, lat)
	x, y = x - offsetX, y - offsetY
	print('node \"' + node + ' X: ' + str(x) + ', Y: ' + str(y) + ". No. of packets: " +
		  str(len(keptNodesMethodTimo[node])))


print('\nConsiderable nodes sending frequently at several periodicities: (Direct method): ')
for node in keptNodesMethodMostafa:
	lon = keptNodesMethodMostafa[node].__getitem__(0).__getattribute__('lon')
	lat = keptNodesMethodMostafa[node].__getitem__(0).__getattribute__('lat')
	x, y = proj.transform(proj_WGS84, proj_CH1903, lon, lat)
	x, y = x - offsetX, y - offsetY
	print('node \"' + node + '\": X: ' + str(x) + ', Y: ' + str(y) + ". No. of packets: " +
		  str(len(keptNodesMethodMostafa[node])))


# plotting the periodicity distribution
plot.plot(periodicityDistribution)
plot.title("periodicityDistribution")
plot.xlabel("periodicities (2 h to 2 weeks), one hour in between two succeeding indices")
plot.ylabel("number of end devices per periodicity-hour")
plot.show()

# stopping the timer:
time_stop = time.clock()

# printing the execution time
print("\n\nexecution time: " + str(time_stop - time_start))
