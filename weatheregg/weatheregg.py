
import sys
from ast import literal_eval
from collections import OrderedDict
from pathlib import PurePath
from os import path, makedirs
import typing as T
import logging
import csv
import time
import datetime
import re
import pytz

import bs4 as bs
import requests


FILE_NAME = 'current_weather.csv'
FILE_PATTERN = "{0:%Y_%m_%d_%H_%M}.csv"
DATA_DIR_NAME = 'weather_back_log'

TIMESTAMP_FORMAT = '%Y-%m-%d %H:%M'
TIMESTAMP_PATTERN = '{{0:{}}}'.format(TIMESTAMP_FORMAT)

# wetter.at url pattern:
WETTER_AT = 'http://www.wetter.at/wetter/'
WETTER_AT += '{country}/{state}/{location}/prognose/48-stunden'


class WeathereggException(Exception):
    pass


class LocationError(WeathereggException):
    """
    Invalid location
    """


class ParseError(WeathereggException):
    pass


def get_response_for_location(country: str,
                              state: str,
                              location: str) -> requests.Response:
    """
    This class makes a request to wetter.at to get the current weather
    data for the provided location.
    :param country:
    :param state:
    :param location:
    :return:
    """
    if any(len(s) == 0 or
           s is None or
           not isinstance(s, str)
           for s in (country, state, location)):
        msg = 'country, state and location can not be empty or None and ' \
              'they must be strings.'
        raise TypeError(msg)

    country = country.strip().lower()
    state = state.strip().lower()
    location = location.strip().lower()

    url = WETTER_AT.format(country=country,
                           state=state,
                           location=location)

    # print('[INFO] Make request `{}`'.format(url))

    response = requests.get(url)

    if response.status_code != 200:
        msg = '{} not found! Got status code {}'.format(
            url, response.status_code
        )
        raise requests.HTTPError(msg)

    else:
        return response


def parse_chart(weather_soup: bs.BeautifulSoup,
                chart_name: str) -> tuple:
    """
    This function takes the soup, searches for the chart and returns
    a list of chart values.

    :param weather_soup:
    :param chart_name:
    :return:
    """
    if chart_name not in ('temp', 'rain', 'cloudcov', 'wind'):
        msg = 'chart name must be in ("temp", "rain", "cloudcov", "wind").'
        msg += ' Got {chart_name}'
        msg = msg.format(chart_name=chart_name)
        raise ValueError(msg)

    # Sadly the website has the data only available in a js script.
    # So we need to parse the data out of there.
    # Luckily the data is all in one line. So it is only necessary to
    # search for the lines which contain `setDataArray`.
    chart_id = 'tab-' + chart_name
    chart = weather_soup.find(
        'div', {'id': chart_id}
    )

    if chart is None:
        msg = 'No data found for the provided location!'
        raise LocationError(msg)

    data_lines = [line for line in chart.text.splitlines()
                  if 'setDataArray' in line]
    #
    # if len(data_lines) < 1:
    #     msg = 'No data found for {}'
    #     raise ValueError(msg.format(chart_name))

    data_line = data_lines[0]

    # we match greedy.
    data_pattern = re.compile(r'\[\[[\d\s\[\],.\-]*\]\]')

    data = data_pattern.search(data_line)

    if data is None:
        msg = 'The regular expression did not match the data for some ' \
              'reason. Please check the regex.'
        raise ParseError(msg)

    data = data.group()
    # use literal_eval to convert the string to a list.
    # string has form of '[[0, 10], [1, 12], ..., [47, 9]]'
    data = literal_eval(data)

    # for some reason there are double entries in the list
    # so we need to clean the data.
    # this would be possible with sets, though I am scared that
    # the values differ somehow. So I iterate over the values.
    cleaned_data = OrderedDict()
    for d in data:
        if d[0] not in cleaned_data:
            cleaned_data[d[0]] = d[1]

    msg = 'Apparently the data can also miss entries. Got {} instead of 48'
    msg = msg.format(str(len(cleaned_data)))
    assert len(cleaned_data) == 48, msg

    return tuple(cleaned_data.values())


def create_datetime_list(data: T.Tuple[tuple, tuple, tuple, tuple],
                         tz: T.Union[datetime.tzinfo, None] = None) -> tuple:
    """
    Takes a tuple of lists and adds a list with date and one with the hour.
    :param data:
    :param tz:
    :return: 
    """
    # Timezones are not supported right now.
    current_time = datetime.datetime.now(tz=tz)
    current_time = current_time.replace(minute=0, second=0, microsecond=0)

    time_list = []
    for hour, *data in enumerate(zip(*data)):
        t = current_time + datetime.timedelta(hours=hour)
        timestamp = TIMESTAMP_PATTERN.format(t)
        time_list.append(timestamp)

    return tuple(time_list)


def get_weather_for_location(country: str,
                             state: str,
                             location: str,
                             tz: T.Union[datetime.tzinfo, None] = None) -> \
        T.Tuple[tuple, tuple, tuple, tuple, tuple]:
    """
    Returns a tuple containing the following data:

    - datetime in hours
    - temperature in °C
    - cloudiness in %
    - precipitation in mm
    - wind velocity in km/h

    :param country:
    :param state:
    :param location:
    :param tz:
    :return:
    """

    response = get_response_for_location(country, state, location)
    weather_soup = bs.BeautifulSoup(response.content, 'lxml')

    temp_data = parse_chart(weather_soup, 'temp')
    rain_data = parse_chart(weather_soup, 'rain')
    cloudcov_data = parse_chart(weather_soup, 'cloudcov')
    wind_data = parse_chart(weather_soup, 'wind')

    datetime_list = create_datetime_list(
        (temp_data, cloudcov_data, rain_data, wind_data),
        tz=tz
    )

    return datetime_list, temp_data, cloudcov_data, rain_data, wind_data


def save_data_to_csv(data: T.Tuple[tuple, tuple, tuple, tuple, tuple],
                     file_path: T.Union[str, PurePath]) -> None:
    """
    Function to write data to a csv file

    :param data:
    :param file_path:
    :return:
    """

    file_path = str(file_path)
    file_path = str(path.abspath(file_path))

    with open(file_path, 'w') as f:
        csv_writer = csv.writer(f, delimiter=',')

        # write header
        csv_writer.writerow([
            '',
            'temperature',
            'cloudiness',
            'precipitation',
            'wind_velocity'
        ])

        # write data
        for d in zip(*data):
            csv_writer.writerow(d)


def save(data: T.Tuple[tuple, tuple, tuple, tuple, tuple],
         dir_path: T.Union[str, PurePath],
         tz: T.Union[datetime.tzinfo, None] = None) -> None:
    """
    Function to save the data. First to the current
    file and then to the data directory.

    :param data:
    :param dir_path:
    :param tz:
    :return:
    """

    dir_path = str(dir_path)
    dir_path = str(path.abspath(dir_path))

    back_log_dir = str(path.join(dir_path, 'weather_back_log'))

    makedirs(dir_path, exist_ok=True)
    makedirs(back_log_dir, exist_ok=True)

    # save the current data
    file_path = path.join(dir_path, FILE_NAME)
    save_data_to_csv(data=data, file_path=file_path)

    dd = datetime.datetime.now(tz=tz)
    dd = dd.replace(minute=0, second=0, microsecond=0)

    back_log_file_name = FILE_PATTERN.format(dd)
    back_log_file_path = path.join(back_log_dir, back_log_file_name)

    # if path.isfile(back_log_file_path):
    #     msg = '{} does already exist! cannot overwrite backlog file!'
    #     raise FileExistsError(msg.format(str(back_log_file_path)))

    save_data_to_csv(data=data, file_path=back_log_file_path)


def _clean_location(location: str):
    location = location.lower().strip()
    location = location.replace('ä', 'ae')
    location = location.replace('ö', 'oe')
    location = location.replace('ü', 'ue')
    location = location.replace('ß', 'ss')
    location = location.replace(' ', '-')

    return location


class WeatherEgg:
    """
    Main Class of the program.
    Its run_forever method starts a loop which collects data and saves it to
    the current_weather file and to the weather_back_log directory. You need
    to provide a data directory path for it to work though.

    Usage::
        >>> weatheregg = WeatherEgg(
        ...     'oesterreich',
        ...     'niederoesterreich',
        ...     'moedling',
        ...     data_dir='/home/user/data/'
        ... )

        >>> weatheregg.weather_forecast()  # doctest: +ELLIPSIS
        {'timestamp': ...}

        >>> weatheregg.current_temperature()  # doctest: +SKIP
        >>> weatheregg.current_cloudiness()  # doctest: +SKIP
        >>> weatheregg.current_precipitation()  # doctest: +SKIP
        >>> weatheregg.current_wind_velocity()  # doctest: +SKIP
        >>> weatheregg.run_forever()  # doctest: +SKIP

    """

    RETRY_INTERVAL = 120  # seconds

    LINE_FORMAT = '{datetime:<16}, {temp:>18}, {cloudiness:>15}, ' \
                  '{precipitation:>18}, {wind:>20}'

    def __init__(self,
                 country: str,
                 state: str,
                 location: str,
                 data_dir: T.Union[str, PurePath, None]=None,
                 tz: T.Union[datetime.tzinfo, None, str]=None,
                 interval: int = 60):
        interval = int(interval)
        if interval < 60:
            msg = 'Interval must be bigger than 60 minutes!'
            raise ValueError(msg)

        if data_dir is not None:
            self._data_dir = str(data_dir)
            self._data_dir = str(path.abspath(data_dir))
        else:
            self._data_dir = None

        if isinstance(tz, str):
            tz = pytz.timezone(tz)

        self._country = _clean_location(country)
        self._state = _clean_location(state)
        self._location = _clean_location(location)
        self._tz = tz
        self._interval = interval

        # check if the location exists:
        get_weather_for_location(
            self._country,
            self._state,
            self._location,
            tz=self._tz
        )

    @property
    def url(self) -> str:
        """
        Returns the url which is used for requesting the weather.

        :return:
        """
        return WETTER_AT.format(
            country=self._country,
            state=self._state,
            location=self._location
        )

    def _get_data(self) -> T.Tuple[tuple, tuple, tuple, tuple, tuple]:
        data = get_weather_for_location(
            self._country,
            self._state,
            self._location,
            tz=self._tz
        )

        return data

    def weather_forecast(self) -> dict:
        """
        Returns the 48 hours weather forecast.

        :return:
        """
        data = self._get_data()
        forecast = {
            'timestamp'    : data[0],
            'temperature'  : data[1],
            'cloudiness'   : data[2],
            'precipitation': data[3],
            'wind_velocity': data[4]
        }
        timestamps = [datetime.datetime.strptime(dd, TIMESTAMP_FORMAT) for
                      dd in forecast['timestamp']]
        if self._tz is not None:
            for dd in timestamps:
                dd.replace(tzinfo=self._tz)
        forecast['timestamp'] = tuple(timestamps)
        return forecast

    def current_weather(self) -> T.Tuple[int, int, float, int]:
        """
        Returns a tuple with the current weather data.
        :return:
        """
        data = self.weather_forecast()
        t = data['temperature'][0]
        c = data['cloudiness'][0]
        p = data['precipitation'][0]
        w = data['wind_velocity'][0]
        return t, c, p, w

    def current_temperature(self) -> int:
        """
        Returns the current temperature based on the 48 hours forecast.
        :return:
        """
        t = self.weather_forecast()['temperature']
        return t[0]

    def current_cloudiness(self) -> int:
        """
        Returns the current cloudiness based on the 48 hours forecast.
        :return:
        """
        c = self.weather_forecast()['cloudiness']
        return c[0]

    def current_precipitation(self) -> float:
        """
        Returns the current precipitation based on the 48 hours forecast.
        :return:
        """
        p = self.weather_forecast()['precipitation']
        return float(p[0])

    def current_wind_velocity(self) -> int:
        """
        Returns the current wind velocity based on the 48 hours forecast.
        :return:
        """
        w = self.weather_forecast()['wind_velocity']
        return w[0]

    def print_weather(self, pretty_print=True) -> None:
        """
        Outputs the weather forecast in a pretty format.
        :return:
        """

        if pretty_print:
            print_format = self.LINE_FORMAT
        else:
            print_format = '{datetime},{temp},{cloudiness},' \
                           '{precipitation},{wind}'

        data = self._get_data()
        print(print_format.format(
            datetime='',
            temp='temperature [°C]',
            cloudiness='cloudiness [%]',
            precipitation='precipitation [mm]',
            wind='wind velocity [km/h]'
        ))

        for d in zip(*data):
            print(print_format.format(
                datetime=d[0],
                temp=str(d[1]),
                cloudiness=str(d[2]),
                precipitation=str(float(d[3])),
                wind=str(d[4])
            ))

    def run_forever(self) -> None:
        """
        This method runs the weatheregg.

        :return:
        """

        if self._data_dir is None:
            msg = 'Please provide a data directory for Weatheregg.'
            raise ValueError(msg)

        makedirs(self._data_dir, exist_ok=True)

        logging_file_path = str(path.join(self._data_dir, 'weatheregg.log'))

        logger = logging.getLogger('weatheregg_logger')
        logger.setLevel(logging.DEBUG)
        fh = logging.FileHandler(logging_file_path)
        fh.setLevel(logging.INFO)
        ch = logging.StreamHandler()
        ch.setLevel(logging.INFO)
        # create formatter and add it to the handlers
        formatter = logging.Formatter(
            '[%(levelname)s] - %(asctime)s - %(message)s')
        fh.setFormatter(formatter)
        ch.setFormatter(formatter)
        # add the handlers to the logger
        logger.addHandler(fh)
        logger.addHandler(ch)

        retry = False

        while True:
            try:
                logger.info('Load data from {}.'.format(self.url))
                data = self._get_data()

            except WeathereggException as fatal_error:
                logger.exception(fatal_error)
                sys.exit(status=1)

            except Exception as error:
                logger.exception(error)
                retry = True

            else:
                logger.info('Save weather data to {}.'.format(self._data_dir))
                try:
                    save(data, dir_path=self._data_dir)
                except Exception as error:
                    logger.exception(error)
                    sys.exit(status=1)

            if retry:
                logger.info('Last request failed. Retry in {} '
                            'seconds'.format(self.RETRY_INTERVAL))
                time.sleep(self.RETRY_INTERVAL)
                retry = False
            else:
                logger.info('Success. Next update in {} minutes.'.format(
                    self._interval))
                time.sleep(self._interval * 60)
