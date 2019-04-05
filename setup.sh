#!/bin/bash
echo "=========== NodeExtractor python setup ==========="
echo -e "\nCreating virtual environment for python3.6 directory venv/ ..."
mkdir venv
virtualenv -q -p /usr/bin/python3.6 venv/
echo -e "Virtual environment successfully set up!\n"
source venv/bin/activate
echo -e "Downloading & installing python dependencies ...\n"
pip install s2sphere datetime matplotlib pyproj
echo -e "\nPlease check, if pip did not raise any errors while installing the following dependencies:"
echo "s2sphere datetime matplotlib pyproj"
echo -e "\n====== NodeExtractor python setup complete! ======\n"
echo "Please execute '$ source venv/bin/activate' and then '$ python3.6 nodeExtractor.py' to run the application."