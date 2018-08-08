"""
This file contains the Weatheregg.
The Weatheregg can make a 48 hours forecast for any location which has the
48 hours forecast available an wetter.at.
Furthermore it can record the data for later analysis.
"""


from weatheregg.weatheregg import WeatherEgg

from weatheregg.version import __version__


__author__ = "Sebastian Schaffer"
__license__ = "MIT"
__status__ = "Production"

__all__ = ('WeatherEgg', )

