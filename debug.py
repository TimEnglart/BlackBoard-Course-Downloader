from blackboard import BlackBoardContent, BlackBoardClient, BlackBoardAttachment, BlackBoardEndPoints, \
    BlackBoardCourse, BlackBoardInstitute
import os
import re
import requests
import datetime
import xmltodict
import argparse
import sys
import json
import getpass
import main

def test():
    args = main.handle_arguments(True)
    # Institute Data
    print("Dumping Institute Properties...")
    institute_data = dict()
    institute_vars = vars(args.institute)
    for item in institute_vars:
        institute_data[item] = institute_vars[item]
    print("Dumped Institute Properties...")
    # Client Data
    client_data = dict()
    client = BlackBoardClient(username=args.username, password=args.password, site=args.site, save_location=args.location, institute=args.institute)
    attempt = client.login()
    print(f"Client Login {'Successful' if attempt[0] else 'Failure'}...\nDumping Client Properties...")
    client_data["public_api_available"] = client.public_endpoint_available()
    client_data["login_endpoint"] = attempt[1].url
    client_data["login_status_code"] = attempt[1].status_code
    client_data["login_response"] =  attempt[1].text
    client_data["successful_login"] = attempt[0]
    client_vars = vars(client)
    for item in client_vars:
        if item not in ('_BlackBoardClient__password', 'session', 'institute', 'api_version', 'thread_pool'):
            client_data[item] = client_vars[item]
    print("Dumped Client Properties...")
    # Get Parent Course Data
    course_data = {
        'endpoint': '',
        'status_code': '',
        'response': '',
        'courses': []
    }

    def get_courses():
        """
        Get all Available Course Information for the Client and Record Details
        """
        courses_request = client.send_get_request(BlackBoardEndPoints.get_user_courses(client.user_id))
        courses = courses_request.json()
        course_data['endpoint'] = courses_request.url
        course_data['status_code'] = courses_request.status_code
        course_data['response'] = courses
        if "results" in courses:
            for course in courses["results"]:
                try:
                    course_request = client.send_get_request(BlackBoardEndPoints.get_course(course["courseId"]))
                    course = course_request.json()
                    bbcourse = BlackBoardCourse(client, course)
                    course_vars = vars(bbcourse)
                    course_sub_data = dict()
                    course_sub_data["course_endpoint"] = course_request.url
                    course_sub_data['status_code'] = course_request.status_code
                    for item in course_vars:
                        course_sub_data[item] = str(course_vars[item])
                    course_data['courses'].append(course_sub_data)
                except Exception as e:
                    course_data['courses'].append({'error': str(e)})

    print("Getting Course Data...")
    get_courses()
    print("Completed Course Data...")
    dumps = {
        'institute': institute_data,
        'client': client_data,
        'courses': course_data,
    }
    print("Preparing to Dump Debug...")
    with open(os.path.abspath(os.path.join(client.base_path, "dump.json")), 'w+') as file:
        print(f"Writing File: \"{file.name}\"...")
        json.dump(dumps, file)
    print("Done...")


if __name__ == "__main__":
    test()
