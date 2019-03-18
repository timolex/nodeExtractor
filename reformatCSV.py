import csv


inputFilename = "periodicities_noZeroes.csv"
outputFilename = "periodicity_frequencies.csv"

outputFile = open(outputFilename, "w+")
outputFile.write("periodicityHour,count\n")

with open(inputFilename, 'r') as inputFile:
	reader = csv.reader(inputFile)

	next(inputFile)

	for line in reader:
		frequency = int(line[1])
		for i in range(frequency):
			outputFile.write(line[0] + ",1\n")


outputFile.close()
