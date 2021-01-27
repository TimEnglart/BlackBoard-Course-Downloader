"""
Main Module is the Main CLI Application
"""
from typing import Optional, Any, List, Union
from blackboard import BlackBoardContent, BlackBoardClient, BlackBoardAttachment, BlackBoardInstitute, \
    BlackBoardCourse, DownloadQueue
import argparse
import sys
import json
import os
import getpass
import signal


# TODO: Add Inline Comments Explaining Possibly Confusing or Dumb Implementations


def get_arguments() -> argparse.Namespace:
    """
    Reads the Arguments Passed into The Script
    :return: The Parsed and Default Arguments
    """
    parser = argparse.ArgumentParser(
        description='Command-line Application that Downloads and Navigates Blackboard Content')

    parser.add_argument("-v", "--version", help="Displays Application Version", action="store_true")
    parser.add_argument("-g", "--gui", help="Use GUI instead of CLI", action="store_true")
    parser.add_argument("-m", "--mass-download", help="Download All Course Documents", action="store_true")
    parser.add_argument("-u", "--username", help="Username to Login With")
    parser.add_argument("-p", "--password", help="Password to Login With")
    parser.add_argument("-s", "--site", help="Base Website Where Institute Black Board is Located")
    parser.add_argument("-l", "--location", help="Local Path To Save Content", default='.')
    parser.add_argument("-c", "--course", help="Course ID to Download")
    parser.add_argument("-r", "--record", help="Create A Manifest For Downloaded Data", action="store_true",
                        default=True)
    parser.add_argument("-b", "--backup", help="Keep Local Copy of Outdated Files", action="store_true", default=False)
    parser.add_argument("-V", "--verbose", help="Print Program Runtime Information", action="store_true")
    parser.add_argument("-C", "--config", help="Location of Configuration File", default='.')
    parser.add_argument("-i", "--ignore-input", help="Ignore Input at Runtime", action="store_true")
    parser.add_argument("-t", "--threaded", help="Enable multi-threaded downloading", action="store_true", default=True)
    parser.add_argument("-n", "--num-threads", help="Max Number of Threads to Use When Downloading", default=4)
    return parser.parse_args()


def handle_arguments(debug=False) -> None:
    """
    Uses the Given CLI Arguments, Configuration File and User Input to Fill in the Required Values
    """
    args = get_arguments()
    script_directory = os.path.dirname(os.path.abspath(__file__))
    if args.version:
        print("Application Version: v{}".format("1.0.0"))
        sys.exit(0)

    # Config Will Always Be Relative to Script Location Directory Unless Absolute Path is Provided
    args.config = os.path.abspath(os.path.join(script_directory, args.config, "config.json"))

    print(f"Loading Configuration File: {args.config}")
    config_content = {}
    if os.path.isfile(args.config):
        try:
            with open(args.config) as json_file:
                config_content = json.load(json_file)
        except IOError:
            print("Unable to Read File at Location: {}".format(args.config))
        except json.JSONDecodeError:
            print("Unable to Parse Configuration File: {}".format(args.config))

    # Handle Saving Location
    # TODO: Do we want it to also be relative to the script path if no abs path or do we want it from the working dir
    args.location = os.path.abspath(os.path.join(script_directory, args.location))
    print(f"Saving Content To: {args.location}\n")

    # Command Line Arg -> Config File -> Input

    if args.username is None:
        possible_username = config_content.get('username', '')
        if not args.ignore_input:
            args.username = input(
                "Enter Username [{}]: ".format(possible_username))
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
            args.site = input(
                "Enter Black Board Host Website [{} or 'c' to Search]: ".format(possible_site))

        if ((not args.site or not args.site.strip()) and not possible_site and not args.ignore_input) or \
                args.site == 'c':
            args.site = navigation(options=BlackBoardInstitute.find(input("Institute Name: ")),
                                   attribute='name', sort=True).display_lms_host
            if args.site is None:
                print("No Site Supplied!")
                sys.exit(0)
        else:
            args.site = possible_site
        if args.site:
            args.institute = BlackBoardInstitute.find(args.site)[0]

    # if args.dump:
    #    pass
    args.additional_courses = config_content.get("additionalCourses", [])

    if debug:
        return args
    # Run Actual Program
    if args.gui:
        # Insert GUI Function Here
        print("No GUI Currently Implemented")
        sys.exit(0)
    else:
        return main(args)


# TODO: Probably Need to Clean the Function Up and the Pathing - It Works tho...


def main(args) -> None:
    """
    The Main Function That is Used to Traverse the Blackboard Content
    :param args: The Parsed Arguments from the CLI, Configuration File and Inputs
    """

    client = BlackBoardClient(username=args.username,
                              password=args.password, site=args.site, thread_count=int(args.num_threads),
                              institute=args.institute, save_location=args.location,
                              use_manifest=args.record, backup_files=args.backup)
    login_resp = client.login()
    if login_resp[0]:
        signal.signal(signal.SIGINT, client.stop_threaded_downloads)  # Hook SIGINT (ctrl + c) so we can kill threads
        if not client.use_rest_api:
            input("Your Blackboard Learn Service Doesn't Support the use of the rest API.\nXML request development is "
                  "currently being worked on and should be available soon...\n\nPress Any Key to Exit")
            sys.exit(0)
        if not client.public_endpoint_available():
            input(
                "The /public/ endpoint of of API is not accessible.\nUnfortunately this is required for this "
                "application to function...\n\nPress Any Key to Exit")
            sys.exit(0)
        save_config(args)
        for course in args.additional_courses:  # Append Additional Courses
            client.add_course(course)
        if args.mass_download:
            try:
                for course in client.courses():
                    if args.course is None or course.id == args.course:  # Download only Specified Course
                        course.download_all_attachments(args.location, args.threaded)
            except DownloadQueue.DownloadQueueCancelled:  # We Have Shutdown The Downloads
                print(f"Cancelling All Remaining Downloads...")
        else:
            navigate(client)
    else:
        if input("FAILED TO LOGIN\n" +
                 f"Username: {args.username}\n" +
                 f"Learn Site: {args.site}\n" +
                 f"Response Status Code: {login_resp[1].status_code}\n" +
                 f"Response Body: {login_resp[1].text}\n\n\n" +
                 "[Enter 'r' to Retry]"
                 ) == 'r':
            clear_console()
            handle_arguments()
    return


def navigate(selected_item: Union[BlackBoardClient, BlackBoardCourse, BlackBoardContent, BlackBoardAttachment],
             path: list = None, error_message='') -> None:
    """
    Used to Determine the Options to Display Based on the Selected Blackboard Object During Runtime

    :param selected_item: The Current
    :param path:
    :param error_message:
    """
    # Selecting New Item Based On Current Item
    clear_console()
    if selected_item is None:
        raise Exception("Unknown Error")
    next_item = None
    if path is None:
        path = []
    current_path(path, str(selected_item))

    print("{}\n{}".format('/'.join(path), "Error: " + error_message + "\n" if error_message else ""))
    error_message = ''
    item_class_name = type(selected_item).__name__

    if item_class_name == "BlackBoardClient":
        selected_item: BlackBoardClient
        # Going Forwards
        next_item = navigation(selected_item.courses(), attribute='name', sort=True, title='Course')

        # Going Backwards
        if next_item is None:
            sys.exit(0)

    elif item_class_name == "BlackBoardCourse":
        selected_item: BlackBoardCourse
        # Sub Selection -> New Item
        options = ["Get Content", "Download All Content"]
        sub_selection = navigation(options, title="Option")

        # Going Forwards
        if sub_selection is not None:
            selected_index = options.index(sub_selection)
            if selected_index == 0:  # Content
                next_item = navigation(selected_item.contents(), attribute='title', sort=True, title='Content')
            elif selected_index == 1:  # Download
                selected_item.download_all_attachments(selected_item.client.base_path)  # Returns None
            else:  # Go Back (Not Required)
                next_item = None
        # Going Backwards
        if next_item is None:
            current_path(path)
            next_item = selected_item.client

    elif item_class_name == "BlackBoardContent":
        selected_item: BlackBoardContent
        # Get Child Content or Attachments
        options = ["Get Child Content", "Get Attachments"]
        sub_selection = navigation(options, title="Option")

        # Going Forward
        if sub_selection is not None:
            selected_index = options.index(sub_selection)
            if selected_index == 0:  # Child Content
                next_item = navigation(selected_item.children(), attribute='title', sort=True, title='Child')
            elif selected_index == 1:  # Attachments
                next_item = navigation(selected_item.attachments(), attribute='file_name', sort=True,
                                       title='Attachment')
            else:
                next_item = None

            if next_item is None:
                next_item = selected_item
                current_path(path, '', -1)
                error_message = "No Content"

        # Going Backwards
        if next_item is None:
            current_path(path)
            # Has No Parent Content (Return Course)
            if selected_item.parent_id is None:
                next_item = selected_item.course
            else:  # Has Parent Content (Return Content)
                parent_content = selected_item.course.get_content(selected_item.parent_id)
                next_item = parent_content

    elif item_class_name == "BlackBoardAttachment":
        selected_item: BlackBoardAttachment
        options = ["Download", "Back"]
        sub_selection = navigation(options, title="Option")
        if sub_selection is not None:
            selected_index = options.index(sub_selection)
            if selected_index == 0:  # Download
                selected_item.download(selected_item.client.base_path)

        # Always Go Back to Attachments Parent
        current_path(path)
        # Originally was navigate(selected_item.content)
        next_item = selected_item.content
        error_message = "Successfully Downloaded: {}".format(selected_item.file_name)

    if next_item is not None:
        # current_path(path)
        navigate(next_item, path, error_message)
    else:  # Somehow not a specified Class
        raise Exception(f"Unknown Class Provided ({item_class_name})")


def navigation(options: List, **kwargs) -> Optional[Any]:
    """
    Displays A List of Options and Handles User Input in Selecting One of the Provided Options
    :param options: List of Options to get a User to Choose From
    :param kwargs: Additional Arguments to Modify how the Options are Displayed

    :keyword attribute: The Object Attribute Name for Each Option to Be Displayed and Sorted by (If Sorted is True)
    :keyword title: A title to Describe the Individual Options Provided
    :keyword input_text: Modify the Selection Text for the Options
    :keyword sort: Sort the Options by their Attribute Name (If attribute is also Provided)

    :return: The Selected Option from the Options or None
    """
    # Handle kwargs
    attribute = kwargs.get('attribute', None)
    title = kwargs.get('title', '')
    input_text = kwargs.get('input', "Enter {} Number to Select ['c' to Exit]: ".format(title))
    sort = kwargs.get('sort', False)

    if sort and attribute is not None:
        options = sorted(options, key=lambda element: getattr(element, attribute))
    if not options:
        return None  # No Options to Chose From
    while True:
        for i in range(len(options)):
            print("[{}] {}".format(i + 1, getattr(options[i], attribute) if attribute is not None else str(options[i])))
        choice = input(input_text + "\n")
        if choice.isalpha():
            return None  # No Choice Made
        try:
            choice = int(choice)
            if choice > len(options) or choice <= 0:
                raise ValueError
            return options[choice - 1]  # maybe just return the index
        except (TypeError, ValueError):
            print("Invalid Selection")


def current_path(path: list = None, addition: str = '', step: int = -2) -> None:
    """
    Janky Function to Step Forward or Backwards for Visual Content Traversal When Navigating
    :param path: The Current Path
    :param addition: String to Append to the Current Path
    :param step: How Far to Step Backwards in the Pathing
    """
    if addition:
        path.append(addition)
    else:
        del path[step:]


def save_config(args) -> None:
    """
    Dumps the Required Properties into the Config.json file
    :param args: The Parsed Command-line Arguments
    """
    config = {
        'username': args.username,
        # 'password': args.password,
        'site': args.site,
        'additionalCourses': args.additional_courses
    }
    with open(args.config, 'w+') as save:
        json.dump(config, save)


def clear_console() -> None:
    """
    Clears the Console Output
    """
    os.system('cls' if os.name == 'nt' else 'clear')


if __name__ == "__main__":
    handle_arguments()
