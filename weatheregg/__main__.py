import argparse
import sys

import pytz

from weatheregg import WeatherEgg
from weatheregg.version import __version__ as version


HELP_MSG = "Country, state and location correspond to the information in " \
           "the wetter.at url. E. g.: " \
           "http://www.wetter.at/wetter/oesterreich/" \
           "niederoesterreich/zwettl/prognose/48-stunden."


def forecast(args=None) -> None:
    """
    Retrieves 48 hours weather data from wetter.at for the given location.

    :return:
    """

    if args is None:
        args = sys.argv[1:]

    parser = argparse.ArgumentParser(
        description='WeatherEgg-{}'.format(version),
        prog='weatheregg-forecast'
    )

    parser.add_argument('country')
    parser.add_argument('state')
    parser.add_argument('location', help=HELP_MSG)

    parser.add_argument('-t', '--timezone',
                        help='E. g. Europe/Vienna. You need to specify the '
                             'timezone if the location does not have your '
                             'local timezone'
                        )

    parser.add_argument('-p', '--pretty-format',
                        default=False,
                        action='store_true',
                        help='outputs the Forecast in a pretty format '
                             'instead of plain csv.'
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

    weatheregg.print_weather(pretty_print=args.pretty_format)


def current_weather(args=None) -> None:
    """
    Prints the current temperature for the specified location.
    :param args:
    :return:
    """

    if args is None:
        args = sys.argv[1:]

    parser = argparse.ArgumentParser(
        description='WeatherEgg-{}'.format(version),
        prog='weatheregg'
    )

    parser.add_argument('country')
    parser.add_argument('state')
    parser.add_argument('location', help=HELP_MSG)

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
        prog='weatheregg-recorder'
    )

    parser.add_argument('country')
    parser.add_argument('state')
    parser.add_argument('location', help=HELP_MSG)

    parser.add_argument(
        'directory',
        help='Where do you want to store the data? Be careful to not store '
             'data from two weathereggs into the same directory, since they '
             'will overwrite each other.'
    )

    parser.add_argument(
        '-i', '--interval',
        type=int,
        default=60,
        help='In which intervals do you want to update the data?'
             ' It must be bigger than 60 minutes.'
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
