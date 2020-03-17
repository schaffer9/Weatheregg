import os
from setuptools import setup


version = {}

ROOT_DIR = os.path.abspath(os.path.dirname(__file__))
VERSION_FILE = os.path.join(ROOT_DIR, 'weatheregg', 'version.py')

with open(VERSION_FILE) as fp:
    exec(fp.read(), version)


def read(file_name):
    """
    Utility function to read the README file.
    Used for the long_description.  It's nice, because now 1) we have a top
    level
    README file and 2) it's easier to type in the README file than to put a raw
    string in below ...

    :param file_name:
    :return:
    """

    return open(os.path.join(os.path.dirname(__file__), file_name)).read()


setup(
    name="Weatheregg",
    version=version['__version__'],
    author="Sebastian Schaffer",
    author_email="schaffer.sebastian@gmx.at",
    description="Small program to download some weather data",
    license="MIT",
    packages=['weatheregg'],
    long_description=read('README.md'),
    install_requires=['requests==2.19.1',
                      'pytest==3.6.3',
                      'lxml==4.2.3',
                      'pytz==2018.5'],
    entry_points={
              'console_scripts': [
                  'weatheregg-recorder = weatheregg.__main__:run_weatheregg',
                  'weatheregg-forecast = weatheregg.__main__:forecast',
                  'weatheregg = weatheregg.__main__:current_weather'
              ]
    }
)
