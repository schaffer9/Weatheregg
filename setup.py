import os
from setuptools import setup


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
    version="0.0.1",
    author="Sebastian Schaffer",
    author_email="schaffer.sebastian@gmx.at",
    description="Small program to download some wheather data",
    license="MIT",
    packages=['weatheregg', 'tests'],
    long_description=read('README.md'),
    install_requires=['bs4==4.6', 'requests==2.18', 'pytest==3.2', 'lxml==4.1'],
    entry_points={
              'console_scripts': [
                  'weatheregg = weatheregg.__main__:main'
              ]
    }
)
