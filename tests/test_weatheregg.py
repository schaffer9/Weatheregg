from os import path, mkdir, remove
from shutil import rmtree
import pytest
import unittest
from unittest import mock

import bs4 as bs
import requests

from weatheregg.weatheregg import (
    # main_loop,
    LocationError,
    get_response_for_location,
    parse_chart
    # parse_response
)


TEST_DIR = path.abspath(path.dirname(__file__))
ROOT_DIR = path.abspath(path.join(TEST_DIR, '..'))
DATA_DIR = path.abspath(path.join(ROOT_DIR, 'data'))


class TestGetWeatherForLocation(unittest.TestCase):
    def test_000_pass_valid_location(self):
        response = get_response_for_location('oesterreich ',
                                             'niederoesterreich',
                                             'purkersdorf')

        self.assertEqual(response.status_code, 200)

    def test_001_pass_none(self):

        with self.assertRaises(TypeError):
            get_response_for_location(None, 'niederoesterreich', 'purkersdorf')

        with self.assertRaises(TypeError):
            get_response_for_location('oesterreich', None, 'purkersdorf')

        with self.assertRaises(TypeError):
            get_response_for_location('oesterreich', 'niederoesterreich', None)

    def test_002_pass_empty_str(self):
        with self.assertRaises(TypeError):
            get_response_for_location('', 'niederoesterreich', 'purkersdorf')

        with self.assertRaises(TypeError):
            get_response_for_location('oesterreich', '', 'purkersdorf')

        with self.assertRaises(TypeError):
            get_response_for_location('oesterreich', 'niederoesterreich', '')
    #
    # def test_003_pass_invalid_location(self):
    #     with self.assertRaises(LocationError):
    #         get_response_for_location('bla', 'niederoesterreich',
    #                                   'purkersdorf')
    #
    #     with self.assertRaises(LocationError):
    #         get_response_for_location('oesterreich', 'bla', 'purkersdorf')
    #
    #     with self.assertRaises(LocationError):
    #         get_response_for_location('oesterreich', 'niederoesterreich',
    #                                   'bla')

    def test_004_failed_request(self):
        """
        Checks what happens if a request fails.
        :return:
        """
        with mock.patch('requests.get') as mock_request:
            response = requests.Response()
            response.status_code = 404
            mock_request.return_value = response

            self.assertRaises(requests.HTTPError,
                              get_response_for_location,
                              'oesterreich',
                              'niederoesterreich',
                              'somewhere')


class TestParseChart(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        response = get_response_for_location('oesterreich',
                                             'niederoesterreich',
                                             'purkersdorf')
        cls.weather_soup = bs.BeautifulSoup(response.content, 'lxml')

    def test_000_parse_temp_chart(self):
        data = parse_chart(self.weather_soup, 'temp')
        self.assertEqual(len(data), 48)

    def test_001_parse_rain_chart(self):
        data = parse_chart(self.weather_soup, 'rain')
        self.assertEqual(len(data), 48)

    def test_002_parse_cloudcov_chart(self):
        data = parse_chart(self.weather_soup, 'cloudcov')
        self.assertEqual(len(data), 48)

    def test_003_parse_wind_chart(self):
        data = parse_chart(self.weather_soup, 'wind')
        self.assertEqual(len(data), 48)

    def test_004_invalid_name(self):
        with self.assertRaises(ValueError):
            parse_chart(self.weather_soup, 'test')



# class TestWeatherEgg(unittest.TestCase):
#     @pytest.mark.functional
#     def test_000_main_loop(self):
#         main_loop('wien', '60', DATA_DIR, single_run=True)
#
#         f = path.join(DATA_DIR, 'wien_weather.csv')
#
#         assert path.exists(f)
#
#         remove(f)
#
#     @pytest.mark.functional
#     def test_001_invalid_location(self):
#         with pytest.raises(LocationError):
#             main_loop('monkey_town', '60', DATA_DIR, single_run=True)
#
#         f = path.join(DATA_DIR, 'monkey_town')
#
#         assert not path.exists(f)
#
#     @classmethod
#     def tearDownClass(cls):
#
#         rmtree(DATA_DIR)
#
#
# def test_000_make_request_for_location():
#     wetter_online_request('wien')
#
#
# # def test_001_make_request_for_location_with_wrong_types():
# #     with pytest.raises(TypeError):
# #         wetter_online_request(1)
# #
# #     with pytest.raises(TypeError):
# #         wetter_online_request([1, 2])
# #
# #     with pytest.raises(TypeError):
# #         wetter_online_request(('1', '2'))
# #
# #     with pytest.raises(TypeError):
# #         wetter_online_request(None)
#
#
# # def test_002_parse_response():
# #
# #     response = wetter_online_request('wien')
# #
# #     data = parse_response(response=response)
# #
# #     assert len(data) >= 24
# #     assert len(data[0]) == 6
# #
# #
# # def test_003_parse_response_with_none():
# #
# #     with pytest.raises(ValueError):
# #         data = parse_response(response=None)
# #
