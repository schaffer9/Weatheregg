"""
Weatheregg`s main test file
"""

from os import path, remove
from shutil import rmtree
import datetime
import uuid
import unittest
from unittest import mock

import bs4 as bs
import requests
import pytz

from weatheregg.weatheregg import (
    LocationError,
    get_response_for_location,
    get_weather_for_location,
    # parse_chart,
    save_data_to_csv,
    save,
    DATA_DIR_NAME,
    FILE_NAME,
    FILE_PATTERN,
    WeatherEgg
)

TEST_DIR = path.abspath(path.dirname(__file__))
ROOT_DIR = path.abspath(path.join(TEST_DIR, '..'))
DATA_DIR = path.abspath(path.join(ROOT_DIR, 'data'))


class TestGetResponseForLocation(unittest.TestCase):
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

    def test_003_failed_request(self):
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


# class TestParseChart(unittest.TestCase):
#     @classmethod
#     def setUpClass(cls):
#         """
#
#         :return:
#         """
#         response = get_response_for_location('oesterreich',
#                                              'niederoesterreich',
#                                              'purkersdorf')
#         cls.weather_soup = bs.BeautifulSoup(response.content, 'lxml')
#
#     def test_000_parse_temp_chart(self):
#         data = parse_chart(self.weather_soup, 'temp')
#         self.assertEqual(len(data), 48)
#
#     def test_001_parse_rain_chart(self):
#         data = parse_chart(self.weather_soup, 'rain')
#         self.assertEqual(len(data), 48)
#
#     def test_002_parse_cloudcov_chart(self):
#         data = parse_chart(self.weather_soup, 'cloudcov')
#         self.assertEqual(len(data), 48)
#
#     def test_003_parse_wind_chart(self):
#         data = parse_chart(self.weather_soup, 'wind')
#         self.assertEqual(len(data), 48)
#
#     def test_004_invalid_name(self):
#         with self.assertRaises(ValueError):
#             parse_chart(self.weather_soup, 'test')
#
#     def test_raise_location_error(self):
#         response = get_response_for_location('oesterreich',
#                                              'niederoesterreich',
#                                              'somewhere')
#         weather_soup = bs.BeautifulSoup(response.content, 'lxml')
#         with self.assertRaises(LocationError):
#             parse_chart(weather_soup, 'rain')


def check_file(test_case, file_path):
    """

    :param test_case:
    :param file_path:
    :return:
    """
    with open(file_path, 'r') as file:
        import csv

        data = list(csv.reader(file, delimiter=','))

    header = data[0]

    test_case.assertEqual(
        header,
        [
            '',
            'temperature',
            'cloudiness',
            'rain',
            'wind_velocity'
        ]
    )

    test_case.assertEqual(len(data), 49)

    for row in data[1:]:
        test_case.assertEqual(len(row), 5)
        for v in row[1:]:
            float(v)


class TestSaveDataToCSV(unittest.TestCase):
    def setUp(self):
        """

        :return:
        """
        file_name = str(uuid.uuid4()) + '.csv'
        self.file_path = str(path.join(TEST_DIR, file_name))

    def tearDown(self):
        """

        :return:
        """
        remove(self.file_path)

    def test_000_save_data_to_csv(self):
        data = get_weather_for_location(
            'oesterreich',
            'niederoesterreich',
            'moedling',
        )

        save_data_to_csv(data, self.file_path)

        check_file(self, self.file_path)


class TestSave(unittest.TestCase):
    def setUp(self):
        """

        :return:
        """
        unique_name = str(uuid.uuid4())
        self.data_path = str(path.join(TEST_DIR, unique_name))

    def tearDown(self):
        """

        :return:
        """
        if path.isdir(self.data_path):
            rmtree(self.data_path)

    def test_000_save_data(self):
        data = get_weather_for_location(
            'oesterreich',
            'niederoesterreich',
            'moedling',
            tz=pytz.timezone('Europe/Vienna')
        )

        save(data, self.data_path, tz=pytz.timezone('Europe/Vienna'))

        dd = datetime.datetime.now()
        dd = dd.replace(minute=0, second=0, microsecond=0)
        file_path = path.join(self.data_path, FILE_NAME)
        backlog_dir = path.join(self.data_path, DATA_DIR_NAME)
        backlog_file_name = FILE_PATTERN.format(dd)
        backlog_file_path = path.join(backlog_dir, backlog_file_name)

        self.assertTrue(path.isdir(self.data_path))
        self.assertTrue(path.isdir(backlog_dir))
        self.assertTrue(path.isfile(file_path))
        self.assertTrue(path.isfile(backlog_file_path))

        check_file(self, file_path)
        check_file(self, backlog_file_path)


class TestWeatherEgg(unittest.TestCase):
    def setUp(self):
        """

        :return:
        """
        unique_name = str(uuid.uuid4())
        self.data_path = str(path.join(TEST_DIR, unique_name))

    def tearDown(self):
        """

        :return:
        """
        if path.isdir(self.data_path):
            rmtree(self.data_path)

    def test_000_pass_invalid_location(self):
        with self.assertRaises(LocationError):
            WeatherEgg(
                'somewhere',
                'somewhere',
                'somewhere',
                tz=pytz.timezone('Europe/Vienna')
            )

    def test_001_pass_invalid_interval(self):
        with self.assertRaises(ValueError):
            WeatherEgg(
                'oesterreich',
                'niederoesterreich',
                'purkersdorf',
                interval=0,
            )

    def test_002_check_url(self):
        weatheregg = WeatherEgg(
            'oesterreich',
            'niederoesterreich',
            'purkersdorf',
            tz=pytz.timezone('Europe/Vienna')
        )
        self.assertEqual(
            weatheregg.url,
            'http://www.wetter.at/wetter/oesterreich/'
            'niederoesterreich/purkersdorf/prognose/stuendlich'
        )

    def test_003_weather_forecast(self):
        weatheregg = WeatherEgg(
            'oesterreich',
            'niederoesterreich',
            'purkersdorf',
            data_dir='/data',
            tz=pytz.timezone('Europe/Vienna')
        )
        forecast = weatheregg.weather_forecast()

        for field in ['timestamp', 'temperature', 'cloudiness',
                      'rain', 'wind_velocity']:
            self.assertEqual(len(forecast[field]), 48)

        float(weatheregg.current_cloudiness())
        float(weatheregg.current_rain())
        float(weatheregg.current_temperature())
        float(weatheregg.current_wind_velocity())

    def test_004_run_forever(self):
        weatheregg = WeatherEgg(
            'oesterreich',
            'niederoesterreich',
            'moedling',
        )

        with self.assertRaises(ValueError):
            weatheregg.run_forever()
