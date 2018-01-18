import argparse
import sys

try:
    from weatheregg.weatheregg import main_loop
except ModuleNotFoundError:
    from weatheregg import main_loop


def main(args=None):
    """The main routine."""

    if args is None:
        args = sys.argv[1:]

    parser = argparse.ArgumentParser(description='WeatherEgg-0.0.1', prog='weatheregg')

    parser.add_argument('location', help='Which place?')

    parser.add_argument('directory', help='Where do you want to store your data?')

    parser.add_argument('-i', '--interval', type=int, default=60, help='In which intervals do you want to collect data?'
                                                                       ' Must be given in minutes')

    parser.add_argument('-s', '--single-run', action='store_true', help='Do you want to just load the data once?')

    args = parser.parse_args(args)

    print(args)

    assert args.interval >= 60, 'Interval must be greater than 60 minutes'
    main_loop(location=args.location,
              dir_path=args.directory,
              time_frame=args.interval,
              single_run=args.single_run)


if __name__ == '__main__':
    main()
