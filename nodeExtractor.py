import csv


class Transmission:

	def __init__(self, trans_id, time, lat, lon):
		self.trans_id = trans_id
		self.time = time
		self.lat = lat
		self.lon = lon


# Initializing the dictionary, which will hold all Transmission-objects per key (= nodeaddr)
packetDict = {}


# Parsing the .csv-file
# TODO: change file to actual DB dump
with open('test.csv', 'r') as csv_file:
	csv_reader = csv.reader(csv_file)

	# skipping the first line (fieldnames)
	next(csv_file)

	for line in csv_reader:
		# if for a given key (nodeaddr) no Transmission list exists yet, initialize an empty list at the key (line[2])
		if not (line[2] in packetDict):
			packetDict[line[2]] = []
		packetDict.get(line[2]).append(Transmission(line[0], line[1], line[10], line[11]))

# printing all keys (nodeaddr)
for i in packetDict:
	print(i)

