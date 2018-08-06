from ast import literal_eval
from collections import OrderedDict
from os import path, makedirs
import typing as T
import datetime
import csv
import codecs
import time
import datetime
import re
import pytz

import bs4 as bs
import requests


FILE_NAME = '{location}_weather.csv'
FILE_PATTERN = "{0:%d-%m-%Y_%H}.csv"
DATA_DIR_NAME = 'data'

WETTER_AT = 'http://www.wetter.at/wetter/'
WETTER_AT += '{country}/{state}/{location}/prognose/48-stunden'


class LocationError(Exception):
    """
    Invalid location
    """


# def wetter_online_request(location: str) -> requests.Response:
#     """
#     Makes a request for a specific location
#
#     :param location:
#     :return:
#     """
#
#     if len(location) == 0:
#         raise TypeError
#
#     if isinstance(location, (tuple, dict, set, list, int, float, bool)):
#         raise TypeError
#
#     url = 'https://www.wetteronline.at/{}'.format(location.lower())
#     print('[INFO] Make request `{}`'.format(url))
#
#     request = requests.get(url)
#
#     if request.status_code == 404:
#         raise LocationError
#     if request.status_code != 200:
#         raise requests.exceptions.HTTPError
#     else:
#         return request

#
# def parse_response(response: requests.Response) -> list:
#     """
#     returns a list of selected data:
#     [date, timeframe, temperature, precipitation_probability, wind_velocity]
#
#     :param response:
#     :return:
#     """
#     if response is None:
#         raise ValueError('Response can not be None')
#
#     try:
#         soup = bs.BeautifulSoup(response.content, 'html.parser')
#     except AttributeError:
#         raise TypeError('Response is of type ``'.format(type(response)))
#
#     hourly = soup.find(id='hourly')
#
#     if hourly is None:
#         raise LocationError
#
#     weather_data = [
#         li['data-tt-args'] for li in hourly.find_all(name='li')
#     ]
#     weather_data = [eval(d) for d in weather_data]
#
#     temp_data = [span.text for span in hourly.find_all(
#         name='span',
#         attrs={'class': 'temp'}
#     )]
#     assert len(temp_data) == len(weather_data)
#
#     weather33h = []
#     for d, t in zip(weather_data, temp_data):
#
#         weather = [
#             d[0].split(','),
#             d[2],
#             d[4],
#             d[7]
#         ]
#         # parse the date
#         ti = weather[0][1]
#         date = weather[0][0]
#         ti = ti.strip().split(':')
#         print(d[0])
#         weather[0] = ti[0].strip() + '-' + ti[1].strip()
#
#         today = datetime.date.today()
#         if date == 'heute':
#             date = today
#         elif date == 'morgen':
#             date = today + datetime.timedelta(days=1)
#
#         # add übermorgen
#
#         # parse the values
#         w = weather[2]
#         weather[2] = int(w) if w else 0
#         v = weather[3]
#         weather[3] = int(v) if v else 0
#
#         # add the temperature
#         temp = int(t.strip()[:-1])
#         weather.insert(2, temp)
#
#         # add the date
#         weather.insert(0, date)
#
#         weather33h.append(weather)
#
#     return weather33h


def get_response_for_location(
        country: str,
        state: str,
        location: str
) -> requests.Response:
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

    # # The website does not return a 404 if the location does not exist
    # # It returns its main page instead. The body id though contains the
    # # location if it was found.
    # # It is quite unique. Therefore we check if the id appears in the
    # # response text.
    # body_id = '{country}_{state}'
    # body_id = body_id.format(country=country, state=state)
    #
    # if body_id not in response.text:
    #     msg = '{} was not found'.format(url)
    #     raise LocationError(msg)

    else:
        return response


def parse_chart(
        weather_soup: bs.BeautifulSoup,
        chart_name: str
) -> list:
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
    data_pattern = re.compile(r'\[\[[\d\s\[\],.]*\]\]')

    data = data_pattern.search(data_line).group()
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

    return list(cleaned_data.values())


def create_datetime_list(
        data: T.Tuple[list, list, list, list],
        tz=pytz.timezone('Europe/Vienna')
) -> T.List:
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
        time_list.append(str(t))

    return time_list


def get_weather_for_location(
        country: str,
        state: str,
        location: str,
        tz: datetime.tzinfo=pytz.timezone('Europe/Vienna')
) -> T.Tuple[list, list, list, list, list]:
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


def save_data_to_csv(
        data: T.Tuple[list, list, list, list, list],
        file_path: str
) -> None:
    """
    Function to write data to a csv file

    :param data:
    :param file_path:
    :return:
    """
    file_path = path.abspath(file_path)

    # if not overwrite:
    #     assert not path.exists(file_path), '[INFO] File already exists'

    # if not path.exists(path.dirname(file_path)):
    #     makedirs(path.dirname(file_path))

    with open(file_path, 'w') as f:
        csv_writer = csv.writer(f, delimiter=',')

        # write header
        csv_writer.writerow([
            'datetime',
            'temperature',
            'cloudiness',
            'precipitation',
            'wind_velocity'
        ])

        # write data
        for d in data:
            csv_writer.writerow(d)


# def save_data_to_csv(data: list,
#                      fpath: str,
#                      overwrite: bool = False) -> None:
#     """
#     Function to write data to a csv file
#
#     :param data:
#     :param fpath:
#     :param overwrite:
#     :return:
#     """
#     fpath = path.abspath(fpath)
#
#     if not overwrite:
#         assert not path.exists(fpath), '[INFO] File already exists'
#
#     if not path.exists(path.dirname(fpath)):
#         makedirs(path.dirname(fpath))
#
#     with codecs.open(fpath, 'w', 'utf-8-sig') as f:
#         csv_writer = csv.writer(f, delimiter=',')
#
#         # write header
#         csv_writer.writerow([
#             'date',
#             'time',
#             'weather',
#             'temperature',
#             'precipitation_probability',
#             'wind_velocity'
#         ])
#
#         # write data
#         for d in data:
#             csv_writer.writerow(d)


# def save(data: list, dir_path: str, location: str) -> None:
#     """
#     Function to save the data. First to the current
#     file and then to the data directory.
#
#     :param data:
#     :param dir_path:
#     :param location
#     :return:
#     """
#     dir_path = path.abspath(dir_path)
#
#     assert not path.isfile(dir_path), \
#         '[INFO] Please provide the path to a directory and not a file'
#
#     if not path.isdir(dir_path):
#         print('[INFO] {} does not exist. Creating directory'.format(dir_path))
#         makedirs(dir_path)
#
#     # save the current data
#     fname = FILE_NAME.format(location=location)
#     fpath = path.join(dir_path, fname)
#     save_data_to_csv(data=data, file_path=fpath, overwrite=True)
#
#     # save the data in the data_dir
#     data_dir = path.join(dir_path, DATA_DIR_NAME)
#
#     dd = datetime.datetime.now()
#     fname = location + '_' + FILE_PATTERN.format(dd)
#
#     fpath = path.join(data_dir, fname)
#     save_data_to_csv(data=data, file_path=fpath)

#
# def main_loop(location: str,
#               time_frame: T.Union[int, float],
#               dir_path: str,
#               single_run: bool=False) -> None:
#     """
#     Main loop of weatheregg
#
#     :param location:
#     :param time_frame: in minutes
#     :param dir_path: where you want to store the data
#     :param single_run:
#     :return:
#     """
#     time_frame = int(time_frame)
#     time_frame *= 60
#
#     while True:
#         try:
#             response = wetter_online_request(location=location)
#
#         except (requests.exceptions.RequestException,
#                 requests.exceptions.HTTPError):
#             print('[WARNING] Request failed. No data output')
#             if single_run:
#                 msg = 'not able to reach the website'
#                 raise requests.exceptions.RequestException(msg)
#             time.sleep(time_frame)
#
#         except LocationError:
#             print('[WARNING] Location not found. No data output')
#             if single_run:
#                 msg = 'Location not found'
#                 raise LocationError(msg)
#
#             time.sleep(time_frame)
#
#         else:
#             print('[INFO] Parse response')
#             data = parse_response(response=response)
#             print('[INFO]: Save Data')
#             save(data, dir_path=dir_path, location=location)
#
#             if single_run:
#                 return
#             time.sleep(time_frame)

#
# if __name__ == '__main__':
#     TEST_DIR = path.abspath(path.dirname(__file__))
#     ROOT_DIR = path.abspath(path.join(TEST_DIR, '..'))
#     DATA_DIR = path.abspath(path.join(ROOT_DIR, 'data'))
#
#     main_loop('wien', '60', DATA_DIR, single_run=True)
