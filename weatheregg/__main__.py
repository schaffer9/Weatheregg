import argparse
import sys

import pytz

from weatheregg import WeatherEgg
from weatheregg.version import __version__ as version


def forecast(args=None) -> None:
    """
    Retrieves 48 hours weather data from wetter.at for the given location.

    :return:
    """

    if args is None:
        args = sys.argv[1:]

    parser = argparse.ArgumentParser(
        description='WeatherEgg-1.2.0',
        prog='weatheregg'
    )

    parser.add_argument('country')
    parser.add_argument('state')
    parser.add_argument('location')

    parser.add_argument('-t', '--timezone',
                        help='E. g. Europe/Vienna. You need to specify the '
                             'timezone if the location does not have your '
                             'local timezone'
                        )

    args = parser.parse_args(args)

    if args.timezone is not None:
        tz = pytz.timezone(args.timezone)
    else:
        tz = None

    weatheregg = WeatherEgg(
        country=args.country,
        state=args.state,
        location=args.location,
        tz=tz
    )

    weatheregg.print_weather()


def current_weather(args=None) -> None:
    """
    Prints the current temperature for the specified location.
    :param args:
    :return:
    """

    if args is None:
        args = sys.argv[1:]

    parser = argparse.ArgumentParser(
        description='WeatherEgg-1.2.0',
        prog='weatheregg'
    )

    parser.add_argument('country')
    parser.add_argument('state')
    parser.add_argument('location')

    args = parser.parse_args(args)

    weatheregg = WeatherEgg(
        country=args.country,
        state=args.state,
        location=args.location,
    )

    weather = weatheregg.current_weather()

    f = '{0:<15}: {1}'

    print(f.format('temperature', weather[0]))
    print(f.format('cloudiness', weather[1]))
    print(f.format('precipitation', weather[2]))
    print(f.format('wind_velocity', weather[3]))


def run_weatheregg(args=None):
    """
    This function start the weather record for the specified location.
    """

    if args is None:
        args = sys.argv[1:]

    parser = argparse.ArgumentParser(
        description='WeatherEgg-{}'.format(version),
        prog='weatheregg'
    )

    parser.add_argument('country')
    parser.add_argument('state')
    parser.add_argument('location')

    parser.add_argument(
        'directory',
        help='Where do you want to store your data?'
    )

    parser.add_argument(
        '-i', '--interval',
        type=int,
        default=60,
        help='In which intervals do you want to collect data?'
             ' Must be given in minutes'
    )

    parser.add_argument('-t', '--timezone',
                        help='E. g. Europe/Vienna. You need to specify the '
                             'timezone if the location does not have your '
                             'local timezone')

    args = parser.parse_args(args)

    weatheregg = WeatherEgg(
        country=args.country,
        state=args.state,
        location=args.location,
        tz=args.timezone,
        data_dir=args.directory
    )

    weatheregg.run_forever()
