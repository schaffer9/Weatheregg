from os import path, makedirs
import typing as T
import datetime
import csv
import codecs
import time

import bs4 as bs
import requests


FILE_NAME = '{location}_weather.csv'
FILE_PATTERN = "{0:%d-%m-%Y_%H}.csv"
DATA_DIR_NAME = 'data'


class LocationError(Exception):
    """
    Invalid location
    """


def make_request_for_location(location: str) -> requests.Response:
    """
    Makes a request for a specific location

    :param location:
    :return:
    """

    if len(location) == 0:
        raise TypeError

    if isinstance(location, (tuple, dict, set, list, int, float, bool)):
        raise TypeError

    url = 'https://www.wetteronline.at/{}'.format(location.lower())
    print('[INFO] Make request `{}`'.format(url))

    request = requests.get(url)

    if request.status_code == 404:
        raise LocationError
    if request.status_code != 200:
        raise requests.exceptions.HTTPError
    else:
        return request


def parse_response(response: requests.Response) -> list:
    """
    returns a list of selected data:
    [date, timeframe, temperature, precipitation_probability, wind_velocity]

    :param response:
    :return:
    """
    if response is None:
        raise ValueError('Response can not be None')

    try:
        soup = bs.BeautifulSoup(response.content, 'html.parser')
    except AttributeError:
        raise TypeError('Response is of type ``'.format(type(response)))

    hourly = soup.find(id='hourly')

    if hourly is None:
        raise LocationError

    weather_data = [li['data-tt-args'] for li in hourly.find_all(name='li')]
    weather_data = [eval(d) for d in weather_data]

    temp_data = [span.text for span in hourly.find_all(name='span', attrs={'class': 'temp'})]
    assert len(temp_data) == len(weather_data)

    weather33h = []
    for d, t in zip(weather_data, temp_data):

        weather = [
            d[0].split(','),
            d[2],
            d[4],
            d[7]
        ]
        # parse the date
        ti = weather[0][1]
        date = weather[0][0]
        ti = ti.strip().split(':')
        print(d[0])
        weather[0] = ti[0].strip() + '-' + ti[1].strip()

        today = datetime.date.today()
        if date == 'heute':
            date = today
        elif date == 'morgen':
            date = today + datetime.timedelta(days=1)

        # add übermorgen

        # parse the values
        w = weather[2]
        weather[2] = int(w) if w else 0
        v = weather[3]
        weather[3] = int(v) if v else 0

        # add the temperature
        temp = int(t.strip()[:-1])
        weather.insert(2, temp)

        # add the date
        weather.insert(0, date)

        weather33h.append(weather)

    return weather33h


def save_data_to_csv(data: list, fpath: str, overwrite: bool=False):
    """
    Function to write data to a csv file

    :param data:
    :param fpath:
    :param overwrite:
    :return:
    """
    fpath = path.abspath(fpath)

    if not overwrite:

        assert not path.exists(fpath), '[INFO] File already exists'

    if not path.exists(path.dirname(fpath)):
        makedirs(path.dirname(fpath))

    with codecs.open(fpath, 'w', 'utf-8-sig') as f:
        csv_writer = csv.writer(f, delimiter=',')

        # write header
        csv_writer.writerow(['date', 'time', 'weather', 'temperature', 'precipitation_probability', 'wind_velocity'])

        # write data
        for d in data:
            csv_writer.writerow(d)


def save(data: list, dir_path: str, location: str):
    """
    Function to save the data. First to the current file and then to the data directory

    :param data:
    :param dir_path:
    :return:
    """
    dir_path = path.abspath(dir_path)

    assert not path.isfile(dir_path), '[INFO] Please provide the path to a directory and not a file'

    if not path.isdir(dir_path):
        print('[INFO] {} does not exist. Creating directory'.format(dir_path))
        makedirs(dir_path)

    # save the current data
    fname = FILE_NAME.format(location=location)
    fpath = path.join(dir_path, fname)
    save_data_to_csv(data=data, fpath=fpath, overwrite=True)

    # save the data in the data_dir
    data_dir = path.join(dir_path, DATA_DIR_NAME)

    dd = datetime.datetime.now()
    fname = location + '_' + FILE_PATTERN.format(dd)

    fpath = path.join(data_dir, fname)
    save_data_to_csv(data=data, fpath=fpath)


def main_loop(location: str, time_frame: T.Union[int, float], dir_path: str, single_run: bool=False) -> None:
    """
    Main loop of weatheregg

    :param location:
    :param time_frame: in minutes
    :param dir_path: where you want to store the data
    :param single_run:
    :return:
    """
    time_frame = int(time_frame)
    time_frame *= 60

    while True:
        try:
            response = make_request_for_location(location=location)

        except (requests.exceptions.RequestException,
                requests.exceptions.HTTPError):
            print('[WARNING] Request failed. No data output')
            if single_run:
                msg = 'not able to reach the website'
                raise requests.exceptions.RequestException(msg)
            time.sleep(time_frame)

        except LocationError:
            print('[WARNING] Location not found. No data output')
            if single_run:
                msg = 'Location not found'
                raise LocationError(msg)

            time.sleep(time_frame)

        else:
            print('[INFO] Parse response')
            data = parse_response(response=response)
            print('[INFO]: Save Data')
            save(data, dir_path=dir_path, location=location)

            if single_run:
                return
            time.sleep(time_frame)


if __name__ == '__main__':
    TEST_DIR = path.abspath(path.dirname(__file__))
    ROOT_DIR = path.abspath(path.join(TEST_DIR, '..'))
    DATA_DIR = path.abspath(path.join(ROOT_DIR, 'data'))

    main_loop('wien', '60', DATA_DIR, single_run=True)
