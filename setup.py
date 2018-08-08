import os
from setuptools import setup

from weatheregg.version import __version__


def read(fname):
    """
    Utility function to read the README file.
    Used for the long_description.  It's nice, because now 1) we have a top level
    README file and 2) it's easier to type in the README file than to put a raw
    string in below ...

    :param fname:
    :return:
    """

    return open(os.path.join(os.path.dirname(__file__), fname)).read()

setup(
    name="Weatheregg",
    version=__version__,
    author="Sebastian Schaffer",
    author_email="schaffer.sebastian@gmx.at",
    description="Small program to download some weather data",
    license="MIT",
    packages=['weatheregg', 'tests'],
    long_description=read('README.md'),
    install_requires=['requests==2.19.1',
                      'pytest==3.6.3',
                      'lxml==4.2.3',
                      'beautifulsoup4==4.6.0',
                      'pytz==2018.5'],
    entry_points={
              'console_scripts': [
                  'weatheregg-recorder = weatheregg.__main__:run_weatheregg',
                  'weatheregg-forecast = weatheregg.__main__:forecast',
                  'weatheregg = weatheregg.__main__:current_weather'
              ]
    }
)
