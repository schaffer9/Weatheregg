# Weatheregg
Weatheregg is a simple and useful tool for collecting and saving weather 
data. It uses *wetter.at* and can give a 48 hours forecast for any location 
supported by *wetter.at*.

## Installation:

1. Download and install Python3.6  

2. Download or clone the Weatheregg repository. 

2. Go into the Weatheregg directory and run 

    `$ python36 setup.py install`

3. Run tests to verify your installation:

    `$ pytest`

## Usage:
Weatheregg provides three features:

1. It can give you the current weather data for the specified location:
   
   `$ weatheregg --help`
    
   E. g.: `$ weatheregg Österreich Niederösterreich Mödling` 
   
   **Arguments**: 
   
   
   * Country
   * State 
   * Location
   
     Country, state and location correspond to the information in the wetter.at 
     url. E. g.: 
     http://www.wetter.at/wetter/oesterreich/niederoesterreich/zwettl/prognose/48-stunden.
   

2. It can give you a 48 hours forecast for a specified location:
   
   `$ weatheregg-forecast --help`
   
   E. g.: `$ weatheregg-forecast Österreich Niederösterreich Mödling`
   
   **Arguments**: 
   
   * Country
   * State 
   * Location
   
   **Optional arguments**:
   
   * -t, --timezone:
     If the location lies outside your timezone, you can specify it.
   
   * -p, --pretty-format: outputs the forecast with line alignment.
   
  
3. It can continuously record the 48 hours forecast to csv files. Therefore 
   you also need to specify a data directory. In this directory you will 
   find the logging file, the *current_weather.csv* file and the backlog 
   directory, where all data is saved. The update interval must be bigger 
   than 60 minutes.
   
   `$ weatheregg-recorder --help`
   
   E. g.: 
   `$ weatheregg-recorder Österreich Niederösterreich Mödling 
   /home/user/weatehr_moedling/`
   
   **Arguments**: 
   
   * Country
   * State 
   * Location
   * directory
   
   **Optional arguments**:
   
   * -t, --timezone:
     If the location lies outside your timezone, you can specify it.
     
   * -i, --interval:
     The interval within the data is updated. The default is 60 minutes.
