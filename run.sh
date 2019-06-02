#!/bin/bash

if command -v python3 &>/dev/null; then
	if [ ! -d "./holoplot_venv/" ]; then
		echo Creating Virtual Environment for the dashboard...
		python3 -m venv holoplot_venv
		. ./holoplot_venv/bin/activate
		echo Updating the package manager...
		python -m pip install pip --upgrade
		echo Installing dependencies...
		python -m pip install -r requirements.txt

	else
		. ./holoplot_venv/bin/activate
	fi

	echo Starting the dashboard
	python app.py &
	
	URL="http://0.0.0.0:5000"
	if which xdg-open > /dev/null; then 
		xdg-open $URL
	elif which gnome-open > /dev/null; then
		gnome-open $URL
	fi
else
    echo Installation failed. Python 3 is not installed or was not detected.
fi
