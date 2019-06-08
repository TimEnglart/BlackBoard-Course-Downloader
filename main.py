from blackboard import BlackBoardContent, BlackBoardClient, BlackBoardAttachment, BlackBoardEndPoints, BlackBoardCourse
import argparse
import sys
import json
import os
import getpass


def get_arguments():
    parser = argparse.ArgumentParser(description='')
    parser.add_argument("-v", "--version", help="Displays Application Version", action="store_true")
    parser.add_argument("-g", "--gui", help="Use GUI instead of CLI", action="store_true")
    parser.add_argument("-m", "--mass-download", help="Download All Course Documents", action="store_true")
    parser.add_argument("-u", "--username", help="Username to Login With")
    parser.add_argument("-p", "--password", help="Password to Login With")
    parser.add_argument("-s", "--site", help="Base Website Where Institute Black Board is Located")
    parser.add_argument("-l", "--location", help="Local Path To Save Content")
    parser.add_argument("-c", "--course", help="Course ID to Download")
    parser.add_argument("-d", "--dump", help="Print/Dump All Course Data", action="store_true")
    parser.add_argument("-r", "--record", help="Create A Manifest For Downloaded Data", action="store_true",
                        default=True)
    parser.add_argument("-V", "--verbose", help="Print Program Runtime Information", action="store_true")
    parser.add_argument("-C", "--config", help="Location of Configuration File")

    return parser.parse_args()


def handle_arguments():
    args = get_arguments()
    if args.version:
        print("Application Version: v{}".format("0.0.1"))
        sys.exit(0)

    args.config_file = {}
    if args.config is None and not os.path.isfile('./config.json'):
        args.config = False
    else:  # Load Config
        args.config = './config.json' if args.config is None else args.config
        try:
            with open(args.config) as json_file:
                args.config_file = json.load(json_file)
        except IOError:
            print("Unable to Read File at Location: {}".format(args.config))

    # Command Line Arg -> Config File -> Input
    if args.username is None:
        args.username = args.config_file.get('username', input("Enter Username: "))
        if not args.username.strip():
            print("No Username Supplied!")
            sys.exit(0)

    if args.password is None:
        args.password = args.config_file.get('password', getpass.getpass("Enter Password: "))
        if not args.password.strip():
            print("No Password Supplied!")
            sys.exit(0)

    if args.site is None:
        args.site = args.config_file.get('site', input("Enter Black Board Host Website: "))
        if not args.site.strip():
            print("No Site Supplied!")
            sys.exit(0)

    if args.location is None:
        args.location = './'
    else:
        args.location = input("Enter Save Path: ")
        if not args.location.strip():
            args.location = './'

    if args.course is None:
        pass

    if args.mass_download:
        pass

    if args.record:
        pass

    if args.dump:
        pass

    # Run Actual Program
    if args.gui:
        # Insert GUI Function Here
        print("No GUI Currently Implemented")
        sys.exit(0)
    else:
        return main(args)


def main(args):
    bbc = BlackBoardClient(username=args.username, password=args.password, site=args.site)
    bbc.login()
    return


if __name__ == "__main__":
    handle_arguments()
