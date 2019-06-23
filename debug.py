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
    session = requests.Session()
    # Institute Data
    institute_data = dict()
    institute_vars = vars(args.institute)
    for item in institute_vars:
        institute_data[item] = institute_vars[item]
    # Client Data
    client_data = dict()
    client = BlackBoardClient(username=args.username, password=args.password, site=args.site)

    def login():
        client_data["login_endpoint"] = args.institute.b2_url + "sslUserLogin"
        login_attempt = session.post(args.institute.b2_url + "sslUserLogin",
                                     data={'username': args.username, 'password': args.password})
        client_data["login_status_code"] = login_attempt.status_code
        if login_attempt.status_code == 200:
            client_data["response"] = xmltodict.parse(login_attempt.text)
            xml = xmltodict.parse(login_attempt.text)['mobileresponse']
            if xml['@status'] == 'OK':
                return True
        return False

    attempt = login()
    client_data["successful_login"] = attempt
    client.login()
    client_vars = vars(client)
    for item in client_vars:
        if item not in ('_BlackBoardClient__password', 'session', 'institute', 'api_version'):
            client_data[item] = client_vars[item]
    # Get Parent Course Data
    course_data = {
        'endpoint': '',
        'status_code': '',
        'response': '',
        'courses': []
    }

    def get_courses():
        request = session.get(args.institute.display_lms_host +
                              BlackBoardEndPoints.get_user_courses(client.user_id))
        courses = request.json()
        course_data['endpoint'] = args.institute.display_lms_host + BlackBoardEndPoints.get_user_courses(client.user_id)
        course_data['status_code'] = request.status_code
        course_data['response'] = courses
        if "results" in courses:
            for course in courses["results"]:
                try:
                    bbcourse = BlackBoardCourse(client, course["courseId"])
                    course_vars = vars(bbcourse)
                    course_sub_data = dict()
                    course_sub_data["course_endpoint"] = client.site + BlackBoardEndPoints.get_course(
                        course["courseId"])
                    for item in course_vars:
                        course_sub_data[item] = str(course_vars[item])
                    course_data['courses'].append(course_sub_data)
                except Exception as e:
                    course_data['courses'].append({'error': str(e)})

    get_courses()

    dumps = {
        'institute': institute_data,
        'client': client_data,
        'courses': course_data,
    }
    with open("dump.json", 'w') as file:
        json.dump(dumps, file)


if __name__ == "__main__":
    test()
