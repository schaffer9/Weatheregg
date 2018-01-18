from os import path, mkdir, remove
from shutil import rmtree
import pytest
import unittest

from weatheregg.weatheregg import main_loop, LocationError, make_request_for_location, parse_response


TEST_DIR = path.abspath(path.dirname(__file__))
ROOT_DIR = path.abspath(path.join(TEST_DIR, '..'))
DATA_DIR = path.abspath(path.join(ROOT_DIR, 'data'))


class TestWeatherEgg(unittest.TestCase):
    @pytest.mark.functional
    def test_000_main_loop(self):
        main_loop('wien', '60', DATA_DIR, single_run=True)

        f = path.join(DATA_DIR, 'wien_weather.csv')

        assert path.exists(f)

        remove(f)

    @pytest.mark.functional
    def test_001_invalid_location(self):
        with pytest.raises(LocationError):
            main_loop('monkey_town', '60', DATA_DIR, single_run=True)

        f = path.join(DATA_DIR, 'monkey_town')

        assert not path.exists(f)

    @classmethod
    def tearDownClass(cls):

        rmtree(DATA_DIR)


def test_000_make_request_for_location():
    make_request_for_location('wien')


def test_001_make_request_for_location_with_wrong_types():
    with pytest.raises(TypeError):
        make_request_for_location(1)

    with pytest.raises(TypeError):
        make_request_for_location([1, 2])

    with pytest.raises(TypeError):
        make_request_for_location(('1', '2'))

    with pytest.raises(TypeError):
        make_request_for_location(None)


def test_002_parse_response():

    response = make_request_for_location('wien')

    data = parse_response(response=response)

    assert len(data) >= 24
    assert len(data[0]) == 6


def test_003_parse_response_with_none():

    with pytest.raises(ValueError):
        data = parse_response(response=None)

