import sys
from ast import literal_eval
from pathlib import PurePath
from os import path, makedirs
import typing as T
import logging
import csv
import time
import datetime
import re
import pytz

import requests

FILE_NAME = 'current_weather.csv'
FILE_PATTERN = "{0:%Y_%m_%d_%H_%M}.csv"
DATA_DIR_NAME = 'weather_back_log'

TIMESTAMP_FORMAT = '%Y-%m-%d %H:%M'

# wetter.at url pattern:
WETTER_AT = 'http://www.wetter.at/wetter/'
WETTER_AT += '{country}/{state}/{location}/prognose/stuendlich'


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

    response = requests.get(url)

    if response.status_code != 200:
        msg = '{} not found! Got status code {}'.format(
            url, response.status_code
        )
        raise requests.HTTPError(msg)

    else:
        return response


#
#
# def parse_chart(weather_soup: bs.BeautifulSoup,
#                 chart_name: str) -> tuple:
#     """
#     This function takes the soup, searches for the chart and returns
#     a list of chart values.
#
#     :param weather_soup:
#     :param chart_name:
#     :return:
#     """
#     if chart_name not in ('temp', 'rain', 'cloudcov', 'wind'):
#         msg = 'chart name must be in ("temp", "rain", "cloudcov", "wind").'
#         msg += ' Got {chart_name}'
#         msg = msg.format(chart_name=chart_name)
#         raise ValueError(msg)
#
#     # Sadly the website has the data only available in a js script.
#     # So we need to parse the data out of there.
#     # Luckily the data is all in one line. So it is only necessary to
#     # search for the lines which contain `setDataArray`.
#     chart_id = 'tab-' + chart_name
#     chart = weather_soup.find(
#         'div', {'id': chart_id}
#     )
#     import ipdb
#     ipdb.set_trace()
#     if chart is None:
#         msg = 'No data found for the provided location!'
#         raise LocationError(msg)
#
#     data_lines = [line for line in chart.text.splitlines()
#                   if 'setDataArray' in line]
#     #
#     # if len(data_lines) < 1:
#     #     msg = 'No data found for {}'
#     #     raise ValueError(msg.format(chart_name))
#
#     data_line = data_lines[0]
#
#     # we match greedy.
#     data_pattern = re.compile(r'\[\[[\d\s\[\],.\-]*\]\]')
#
#     data = data_pattern.search(data_line)
#
#     if data is None:
#         msg = 'The regular expression did not match the data for some ' \
#               'reason. Please check the regex.'
#         raise ParseError(msg)
#
#     data = data.group()
#     # use literal_eval to convert the string to a list.
#     # string has form of '[[0, 10], [1, 12], ..., [47, 9]]'
#     data = literal_eval(data)
#
#     # for some reason there are double entries in the list
#     # so we need to clean the data.
#     # this would be possible with sets, though I am scared that
#     # the values differ somehow. So I iterate over the values.
#     cleaned_data = OrderedDict()
#     for d in data:
#         if d[0] not in cleaned_data:
#             cleaned_data[d[0]] = d[1]
#
#     msg = 'Apparently the data can also miss entries. Got {} instead of 48'
#     msg = msg.format(str(len(cleaned_data)))
#     assert len(cleaned_data) == 48, msg
#
#     return tuple(cleaned_data.values())


# def create_datetime_list(data: T.Tuple[tuple, tuple, tuple, tuple],
#                          tz: T.Union[datetime.tzinfo, None] = None) -> tuple:
#     """
#     Takes a tuple of lists and adds a list with date and one with the hour.
#     :param data:
#     :param tz:
#     :return:
#     """
#     # Timezones are not supported right now.
#     current_time = datetime.datetime.now(tz=tz)
#     current_time = current_time.replace(minute=0, second=0, microsecond=0)
#
#     time_list = []
#     for hour, *data in enumerate(zip(*data)):
#         t = current_time + datetime.timedelta(hours=hour)
#         timestamp = TIMESTAMP_PATTERN.format(t)
#         time_list.append(timestamp)
#
#     return tuple(time_list)


def parse_response(response: requests.Response):
    content = response.content.decode("utf-8")

    weather = re.search(r"var locationInfo = (?P<weather>.*);", content)

    if weather is None:
        raise LocationError("Weather data not found. "
                            "The website might have changed or "
                            "there is no information "
                            "for the provided location")
    weather = weather.group("weather")
    weather = literal_eval(weather)
    hourly_data = weather.get('hourly')
    if hourly_data is None:
        raise WeathereggException("Parsing error in data. The data format "
                                  "might have changed.")

    hourly_data = flip_list_of_dicts(hourly_data)
    hourly_data['temp'] = convert_to_int(hourly_data['temp'])
    rename(hourly_data, 'temp', 'temperature')
    hourly_data['wind'] = convert_to_int(hourly_data['wind'])
    rename(hourly_data, 'wind', 'wind_velocity')
    hourly_data['cloud'] = convert_to_int(hourly_data['cloud'])
    rename(hourly_data, 'cloud', 'cloudiness')
    hourly_data['rain'] = convert_to_int(hourly_data['rain'])

    rename(hourly_data, 'periodText', 'timestamp')

    save_del(hourly_data, 'info')
    save_del(hourly_data, 'icon')

    return hourly_data


def rename(d, k_old, k_new):
    d[k_new] = d[k_old]
    save_del(d, k_old)


def is_inter_datetime(dt):
    t0 = dt - datetime.timedelta(3)
    if t0.date() == dt.date():
        return False
    else:
        return True


def get_correct_day(t0, tz=None):
    """
    Is required to determine if the current day is correct.
    Imagine the request is after midnight but you still get the weather
    of 11:00pm.
    """
    current_datetime = datetime.datetime.now(tz=tz)

    day_is_not_correct = is_inter_datetime(current_datetime) and t0 > \
                         datetime.time(20)
    if day_is_not_correct:
        day = current_datetime.date() - datetime.timedelta(1)
    else:
        day = current_datetime.date()
    return day


def time_to_datetime(l, tz=None):
    if not l:
        return []
    n_hours = len(l)
    t0 = datetime.time.fromisoformat(l[0])
    day = get_correct_day(t0, tz=tz)
    d0 = datetime.datetime.combine(day, t0)
    return [d0 + datetime.timedelta(hours=i) for i in range(n_hours)]


def save_del(d, k):
    if k in d.keys():
        del d[k]


def convert_to_int(l):
    return [int(i) for i in l]


def flip_list_of_dicts(l):
    if len(l) == 0:
        raise ValueError("List is empty.")
    return {k: [dic[k] for dic in l] for k in l[0]}


def get_weather_for_location(
        country: str,
        state: str,
        location: str,
        tz: T.Union[datetime.tzinfo, None] = None
) -> dict:
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
    weather = parse_response(response)
    weather['timestamp'] = time_to_datetime(weather['timestamp'], tz)
    return weather


def save_data_to_csv(data: dict,
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
            'rain',
            'wind_velocity'
        ])

        # write data
        time = [t.strftime(TIMESTAMP_FORMAT) for t in data['timestamp']]
        for d in zip(time,
                     data['temperature'],
                     data['cloudiness'],
                     data['rain'],
                     data['wind_velocity']):
            csv_writer.writerow(d)


def save(data: dict,
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
        {...}

        >>> weatheregg.current_temperature()  # doctest: +SKIP
        >>> weatheregg.current_cloudiness()  # doctest: +SKIP
        >>> weatheregg.current_rain()  # doctest: +SKIP
        >>> weatheregg.current_wind_velocity()  # doctest: +SKIP
        >>> weatheregg.run_forever()  # doctest: +SKIP

    """

    RETRY_INTERVAL = 120  # seconds

    LINE_FORMAT = '{datetime}, {temp:>15}, {cloudiness:>15}, ' \
                  '{rain:>18}, {wind:>20}'

    def __init__(self,
                 country: str,
                 state: str,
                 location: str,
                 data_dir: T.Union[str, PurePath, None] = None,
                 tz: T.Union[datetime.tzinfo, None, str] = None,
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

    def _get_data(self) -> dict:
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
        return self._get_data()

    def current_weather(self) -> T.Tuple[int, int, float, int]:
        """
        Returns a tuple with the current weather data.
        :return:
        """
        data = self.weather_forecast()
        t = data['temperature'][0]
        c = data['cloudiness'][0]
        p = data['rain'][0]
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

    def current_rain(self) -> float:
        """
        Returns the current precipitation based on the 48 hours forecast.
        :return:
        """
        p = self.weather_forecast()['rain']
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
                           '{rain},{wind}'

        data = self._get_data()
        print(print_format.format(
            datetime='timestamp',
            temp='         temperature [°C]',
            cloudiness='cloudiness [%]',
            rain='rain [%]',
            wind='wind velocity [km/h]'
        ))
        time = [t.strftime(TIMESTAMP_FORMAT) for t in data['timestamp']]
        for d, t, c, r, w in zip(time,
                                 data['temperature'],
                                 data['cloudiness'],
                                 data['rain'],
                                 data['wind_velocity']):
            print(print_format.format(
                datetime=d,
                temp=str(t),
                cloudiness=str(c),
                rain=str(r),
                wind=str(w)
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
                sys.exit(1)

            except Exception as error:
                logger.exception(error)
                retry = True

            else:
                logger.info('Save weather data to {}.'.format(self._data_dir))
                try:
                    save(data, dir_path=self._data_dir)
                except Exception as error:
                    logger.exception(error)
                    sys.exit(1)

            if retry:
                logger.info('Last request failed. Retry in {} '
                            'seconds'.format(self.RETRY_INTERVAL))
                time.sleep(self.RETRY_INTERVAL)
                retry = False
            else:
                logger.info('Success. Next update in {} minutes.'.format(
                    self._interval))
                time.sleep(self._interval * 60)