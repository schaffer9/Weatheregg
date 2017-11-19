# Weatheregg
A simple program to collect weather data

## Installation:

Download and install Python3.6
Make sure that you have added it to your environment variables and that you can run it

Go into the Weatheregg directory and run

**python setup.py install** or

**python36 setup.py install**


Now you should be able to run the Weatheregg program.

Type **python weatheregg -h**


## usage:
`weatheregg [-h] [-i INTERVAL] [-s] location directory`

| **positional arguments** |
| ------------- |-------------|
| location      | Which place? |
| directory     | Where do you want to store your data? |

| **optional arguments** |
| ------------- |-------------|
| -h, --help                       | show this help message and exit |
| -i INTERVAL, --interval INTERVAL | In which intervals do you want to collect be given in minutes |
| -s, --single-run                 | Do you want to just load the data once? |

Wheatheregg can be run in a loop to collect and update data in a given interval or it is possible to run it just once.

## Examples:

`python -m weatheregg wien data -i 60`

`python -m weatheregg Purkersdorf /home/user/data -s`

`python -m weatheregg Purkersdorf C:\Users\user\workspace\data -i 30`
