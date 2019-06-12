from blackboard import BlackBoardContent, BlackBoardClient, BlackBoardAttachment, BlackBoardEndPoints, \
    BlackBoardCourse, BlackBoardInstitute
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
    parser.add_argument("-l", "--location", help="Local Path To Save Content", default='./')
    parser.add_argument("-c", "--course", help="Course ID to Download")
    parser.add_argument("-d", "--dump", help="Print/Dump All Course Data", action="store_true")
    parser.add_argument("-r", "--record", help="Create A Manifest For Downloaded Data", action="store_true",
                        default=True)
    parser.add_argument("-V", "--verbose", help="Print Program Runtime Information", action="store_true")
    parser.add_argument("-C", "--config", help="Location of Configuration File", default='./config.json')
    parser.add_argument("-i", "--ignore-input", help="Ignore Input at Runtime", action="store_true")
    return parser.parse_args()


def handle_arguments():
    args = get_arguments()
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    if args.version:
        print("Application Version: v{}".format("0.0.1"))
        sys.exit(0)

    config_content = {}
    if os.path.isfile(args.config):
        try:
            with open(args.config) as json_file:
                config_content = json.load(json_file)
        except IOError:
            print("Unable to Read File at Location: {}".format(args.config))
        except json.JSONDecodeError:
            print("Unable to Parse Configuration File: {}".format(args.config))

    # Command Line Arg -> Config File -> Input

    if args.username is None:
        possible_username = config_content.get('username', '')
        if not args.ignore_input:
            args.username = input("Enter Username [{}]: ".format(possible_username))
        if not args.username or not args.username.strip():
            if possible_username:
                args.username = possible_username
            else:
                print("No Username Supplied!")
                sys.exit(0)

    if args.password is None:
        possible_password = config_content.get('password', '')
        if not args.ignore_input:
            args.password = getpass.getpass("Enter Password{}: "
                                            .format(" [Config Password]" if possible_password else ""))
        if not args.password or not args.password.strip():
            if possible_password:
                args.password = possible_password
            else:
                print("No Password Supplied!")
                sys.exit(0)

    if args.site is None:
        possible_site = config_content.get('site', '')
        if not args.ignore_input:
            args.site = input("Enter Black Board Host Website [{} or 'c' to Search]: ".format(possible_site))
        if ((not args.site or not args.site.strip()) and not possible_site and not args.ignore_input) or \
                args.site == 'c':
            args.site = navigation(default=BlackBoardInstitute,
                                   options=BlackBoardInstitute.find(input("Institute Name: ")),
                                   attribute='name', sort=True).display_lms_host
            if args.site is None:
                print("No Site Supplied!")
                sys.exit(0)
        else:
            args.site = possible_site

    if args.location is None:
        pass

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


ARGS = object()


def main(args):
    global ARGS
    ARGS = args
    bbc = BlackBoardClient(username=args.username, password=args.password, site=args.site)
    if bbc.login():
        save_config(args)
        navigate(bbc)
    else:
        if input("Failed to Login [Enter 'r' to Retry]") == 'r':
            main(args)
    return


class SubSelector:
    def __init__(self):
        pass


def current_path(path=None, **kwargs):
    back = kwargs.get('back', False)
    addition = kwargs.get('addition', None)
    if path is None:
        path = []
    if back:
        path = path[:(-2 if 'step' not in kwargs else kwargs['step'])]
    else:
        if addition is not None:
            path.append(addition)
    return path


# Janky AF - unmaintainable
def navigate(chosen_item, previous_item=None, path=None):
    global ARGS
    clear()
    path = current_path(path, addition=str(chosen_item))
    print('/'.join(
        path) + '\n')  # + "\n{}\n-\nCURRENT: {}\nPREVIOUS: {}\n".format((chosen_item.parent_id if hasattr(chosen_item, 'parent_id') else "No Parent") if chosen_item is not None else None, chosen_item, previous_item))
    c_type = type(chosen_item)
    p_type = type(previous_item)
    if c_type.__name__ == "BlackBoardClient":
        new_item = navigation(default=None, options=chosen_item.courses(), attribute='name', sort=True, title='Courses')
        if new_item is None:
            sys.exit(0)
    elif c_type.__name__ == "BlackBoardCourse":
        options = ["Get Content", "Download All Content"]  # Get Course Content
        sub_selection = navigation(default=SubSelector, attribute=None, options=options)
        if type(sub_selection).__name__ != "SubSelector":
            index = options.index(sub_selection)
            if index == 0:  # Content
                new_item = navigation(default=None, options=chosen_item.contents(), attribute='title', sort=True,
                                      title='Content')
            elif index == 1:  # Download
                chosen_item.download_all_attachments(ARGS.location)  # Quits When Done
                new_item = None
        else:
            new_item = None
    elif c_type.__name__ == "BlackBoardContent":
        options = ["Get Child Content", "Get Attachments"]  # Get Child Content or Attachments
        sub_selection = navigation(default=SubSelector, options=options, attribute=None)
        if type(sub_selection).__name__ != "SubSelector":
            index = options.index(sub_selection)
            if index == 1:  # Attachments
                new_item = navigation(default=None, options=chosen_item.attachments(), attribute='file_name', sort=True,
                                      title='Attachment')
                if new_item is None:
                    navigate(chosen_item, previous_item, current_path(path, back=True, step=-1))
            elif index == 0:  # Child Content
                new_item = navigation(default=None, options=chosen_item.children(), attribute='title', sort=True,
                                      title='Child')
                if new_item is None:
                    navigate(chosen_item, previous_item, current_path(path, back=True, step=-1))
        else:
            new_item = None
    elif c_type.__name__ == "BlackBoardAttachment":
        options = ["Download", "Back"]
        sub_selection = navigation(default=SubSelector, options=options, attribute=None)
        if type(sub_selection).__name__ != "SubSelector":
            index = options.index(sub_selection)
            if index == 0:  # Download
                chosen_item.download(ARGS.location)
        new_item = None
    else:
        new_item = None  # Go Back
    # print(new_item.parent_id)
    if new_item is None:
        if previous_item is None:  # Find Parent Content
            if c_type.__name__ == "BlackBoardContent":
                if chosen_item.parent_id is None:
                    navigate(chosen_item._course, None, current_path(path, back=True))
                else:
                    navigate(BlackBoardContent(chosen_item._course, course_id=chosen_item._course.id,
                                               content_id=chosen_item.parent_id), None, current_path(path, back=True))
            elif c_type.__name__ == "BlackBoardAttachment":
                navigate(chosen_item._content, None, current_path(path, back=True))
            elif c_type.__name__ == "BlackBoardCourse":
                navigate(chosen_item._client, None, current_path(path, back=True))
        else:
            # if previous_item is None:

            # else:
            navigate(previous_item, None, current_path(path, back=True))
    else:
        navigate(new_item, chosen_item, path)


def save_config(args):
    config = {
        'username': args.username,
        # 'password': args.password,
        'site': args.site
    }
    with open(args.config, 'w') as save:
        json.dump(config, save)


def navigation(**kwargs):
    # Handle kwargs
    options = kwargs.get('options', [])
    default = kwargs.get('default', object if not options else type(options[0]))
    title = kwargs.get('title', '')
    input_text = kwargs.get('input',
                            "Enter {} Number to Select ['c' to Exit]: ".format(title if title else default.__name__))
    attribute = kwargs.get('attribute', '__name__')
    sort = kwargs.get('sort', False)
    previous = kwargs.get('previous', None)

    if sort:
        options = sorted(options, key=lambda element: getattr(element, attribute))
    if not options:
        print('No Options Present')
        return (default() if default is not None else None) if previous is None else previous
    while True:
        for i in range(len(options)):
            print("[{}] {}".format(i + 1, getattr(options[i], attribute) if attribute is not None else str(options[i])))
        choice = input(input_text)
        print("\n")
        if choice.isalpha():
            return (default() if default is not None else None) if previous is None else previous
        try:
            choice = int(choice)
            if choice > len(options) or choice <= 0:
                raise TypeError
            return options[choice - 1]
        except TypeError:
            print("Invalid Selection")


def clear():
    os.system('cls' if os.name == 'nt' else 'clear')


if __name__ == "__main__":
    handle_arguments()
