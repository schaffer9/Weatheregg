import argparse
import sys

import pytz

from weatheregg import get_weather_for_location


LINE_FORMAT = '{datetime:>25}, {temp:>18}, {cloudiness:>15}, ' \
              '{precipitation:>18}, {wind:>20}'


def get_weather(args=None) -> None:
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

    parser.add_argument('-t', '--timezone', default='Europe/Vienna')

    args = parser.parse_args(args)

    tz = pytz.timezone(args.timezone)

    weather = get_weather_for_location(
        country=args.country,
        state=args.state,
        location=args.location,
        tz=tz
    )
    print(LINE_FORMAT.format(
        datetime='',
        temp='temperature [°C]',
        cloudiness='cloudiness [%]',
        precipitation='precipitation [mm]',
        wind='wind velocity [km/h]'
    ))

    for d in zip(*weather):
        print(LINE_FORMAT.format(
            datetime=d[0],
            temp=str(d[1]),
            cloudiness=str(d[2]),
            precipitation=str(d[3]),
            wind=str(d[4])
        ))

# from weatheregg import main_loop
#
#
# def main(args=None):
#     """The main routine."""
#
#     if args is None:
#         args = sys.argv[1:]
#
#     parser = argparse.ArgumentParser(
#         description='WeatherEgg-0.0.1',
#         prog='weatheregg'
#     )
#
#     parser.add_argument(
#         'location',
#         help='Which place?'
#     )
#
#     parser.add_argument(
#         'directory',
#         help='Where do you want to store your data?'
#     )
#
#     parser.add_argument(
#         '-i', '--interval',
#         type=int,
#         default=60,
#         help='In which intervals do you want to collect data?'
#              ' Must be given in minutes'
#     )
#
#     parser.add_argument(
#         '-s', '--single-run',
#         action='store_true',
#         help='Do you want to just load the data once?'
#     )
#
#     args = parser.parse_args(args)
#
#     print(args)
#
#     assert args.interval >= 60, 'Interval must be greater than 60 minutes'
#     main_loop(location=args.location,
#               dir_path=args.directory,
#               time_frame=args.interval,
#               single_run=args.single_run)
#
#
# if __name__ == '__main__':
#     main()
