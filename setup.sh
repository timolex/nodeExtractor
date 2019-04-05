#!/bin/bash
echo "=========== NodeExtractor python setup ==========="
echo "Creating virtual environment for python3.6 directory venv/ ..."
mkdir venv
virtualenv -q -p /usr/bin/python3.6 venv/
echo "Virtual environment successfully set up!"
source venv/bin/activate
echo "Downloading & installing python dependencies ..."
pip install s2sphere datetime matplotlib pyproj
echo "Please check, if pip did not raise any errors while installing the following dependencies:"
echo "s2sphere datetime matplotlib pyproj"
echo "====== NodeExtractor python setup complete! ======"
echo "Please run '$ python3.6 nodeExtractor.py' to start the application."
