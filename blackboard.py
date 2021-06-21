"""
Blackboard Module Provides the Classes to Interact With the Blackboard Learn Public RESTful API
"""

from __future__ import annotations
import os
import re
from http.cookiejar import CookieJar

import requests
from concurrent import futures
from datetime import datetime
import xmltodict
from urllib.parse import unquote
from colorama import Fore, init
from typing import List, Tuple, Callable, Optional, Dict, Any
import json
import time
import threading
import sys
import browser_cookie3
import http.cookiejar
# import WebScraper

init()




# Thanks to: https://github.com/hako/blackboard-dl for Mobile BB XML Locations

# TODO: Use Consistent Coding Patterns (eg. String Formatting)
# TODO: Reformat Document (Move Nested Classes, etc)


class BlackBoardInstitute:
    """
    A Class To Represent Blackboard Institute (School/University/College) Server
    """

    def __init__(self, data: dict):
        """
        :param data: Response From Learn Institute Lookup (as JSON)
        """
        self._institute_data = data
        self.name = self._institute_data.get('name', None)
        self.id = self._institute_data.get('id', None)
        self.b2_url = self._institute_data.get('b2_url', None)
        self.country = self._institute_data.get('country', None)
        self.has_community_system = self._institute_data.get('has_community_system', None)
        self.username_label = self._institute_data.get('username_label', None)
        self.has_mobile_central = self._institute_data.get('has_mobile_central', None)
        self.http_auth = self._institute_data.get('http_auth', None)
        self.from_people_soft = self._institute_data.get('from_people_soft', None)
        self.client_id = self._institute_data.get('client_id', None)
        self.can_has_ssl_login = self._institute_data.get('can_has_ssl_login', None)
        self.display_lms_host = self._institute_data.get('display_lms_host', None)
        self.access = self._institute_data.get('access', None)
        self.has_planner_license = self._institute_data.get('has_planner_license', None)
        self.prospective_student_access = self._institute_data.get('prospective_student_access', None)
        self.preferred_contact_methods = self._institute_data.get('preferred_contact_methods', None)
        self.has_offline_license = self._institute_data.get('has_offline_license', None)
        self.people_soft_institution_id = self._institute_data.get('people_soft_institution_id', None)
        self.euse = self._institute_data.get('euse', None)
        self.euse_label = self._institute_data.get('euse_label', None)
        self.force_web_login_polling = self._institute_data.get('force_web_login_polling', None)
        self.gcm = self._institute_data.get('gcm', None)

    def __str__(self):
        return "[{}] {} ({}): {}".format(self.country, self.name, self.id, self.display_lms_host)

    def __repr__(self):
        return str(self)

    @staticmethod
    def find(query: str) -> List[BlackBoardInstitute]:
        """
        Looks Up The Specified Query String to Attempt to Find Institutes

        :param query: A String that can be used to Identify a Blackboard Server
        :return: A List Containing all Institutes that Match the Query String
        """
        try:
            response = requests.get("https://mlcs.medu.com/api/b2_registration/match_schools/?",
                                    params={
                                        "q": query,
                                        "language": "en-GB",
                                        "platform": "android",
                                        "device_name": "Android",
                                        "carrier_code": "1337",
                                        "carrier_name": "LEET",
                                    }).text
            xml = xmltodict.parse(response)
            if xml['data'] is not None:
                if type(xml['data']['s']) is list:
                    return [BlackBoardInstitute(data=institute) for institute in xml['data']['s']]
                else:
                    return [BlackBoardInstitute(data=xml['data']['s'])]

        except (xmltodict.ParsingInterrupted, xmltodict.expat.ExpatError, ValueError):  # Some Parsing Error in XML
            _println(f"{Fore.RED}[ERROR] Failed to Parse Institute Response")

        except (requests.exceptions.ConnectionError, requests.exceptions.HTTPError, requests.exceptions.Timeout,
                requests.exceptions.TooManyRedirects):
            _println(f"{Fore.RED}[ERROR] HTTP Error Returned By Institute Lookup")

        return []


class BlackBoardClient:
    """
    Represents The User (Client) Account Session of a Blackboard Server
    """

    def __init__(self, **kwargs):
        """
        :param kwargs: Arguments to Set Certain Client Options
        :keyword username: The Username of the Client to login with
        :keyword password: The Required Password to Login With
        :keyword site: The Website Link to the Base of the LMS
        :keyword institute: The Institute that hosts the LMS
        :keyword thread_count: The Maximum Number of Threads to Create when using Threaded Downloads
        :keyword save_location: The Local System Path to Save Any Downloaded Documents
        :keyword use_manifest: Enables/Disables the Process of Recording Downloaded Document Versions
        :keyword backup_files: Enables/Disables the Process of Keeping Outdated Files when a Newer Version is Downloaded
        """
        self.username = kwargs.get('username', None)
        self.__password = kwargs.get('password', None)
        self.site = kwargs.get('site', None)
        self.login_method = kwargs.get('login_method', 'login')
        self.session = requests.Session()
        self.user_id = None
        self.batch_uid = None
        if self.username is None or self.site is None:
            raise Exception("Missing Username and/or Site")
        if self.__password is None and self.login_method == 'login':
            raise Exception('and/or Password ')
        self.institute = kwargs.get('institute', None)
        self.use_rest_api = True  # Can/Cannot Use The Learn Rest API
        self.api_version = self.LearnAPIVersion("0.0.0")
        self.thread_pool = DownloadQueue(kwargs.get('thread_count', 4))
        self.base_path = kwargs.get('save_location', '.')
        self.additional_courses = []
        self.use_manifest = kwargs.get('use_manifest', True)
        self.backup_files = kwargs.get('backup_files', False)
        self.cookie_jar = CookieJar()

    # XML
    def login(self) -> Tuple[bool, requests.Response]:
        """
        Attempts to Log the User Into the Provided Blackboard Learn Server Using the Specified Username and Password

        :return: Returns a Tuple Containing whether the Login was a Success [0] and the
        Response From the Login Endpoint [1]
        """

        if self.login_method == 'cookie':
            self.cookie_jar = get_cookies(self.site)
            self.session.cookies.update(self.cookie_jar)
            input(f'Cookies:\n{[f"Name: {cookie.name} - Domain: {cookie.domain}" for cookie in self.session.cookies]}')

            r = requests.get(self.site + BlackBoardEndPoints.get_user_by_username(self.username), cookies=self.cookie_jar)
            input(r.status_code)

            login = self.session.get(self.site, cookies=self.cookie_jar)

            resp = self.session.get(self.site + BlackBoardEndPoints.get_user_by_username(self.username),
                                    cookies=self.cookie_jar)
            print(f"Username Response: {resp}")
            if resp.status_code == 200:
                self.user_id = resp.json()["results"][0]["id"]
            return resp.status_code == 200, {}
        else:
            # TODO: On Login Successful Should the Password be unset. But Then Can't Log Back in if 401 Occurs

            if self.institute is None or self.institute.b2_url is None:
                login_endpoint = self.site + "/webapps/Bb-mobile-bb_bb60/"
            else:
                login_endpoint = self.institute.b2_url  # ?v=2&f=xml&ver=4.1.2

            login = self.session.post(login_endpoint + "sslUserLogin",
                                      data={'username': self.username, 'password': self.__password})
        
        if login.status_code == 200:
            input(f'Cookies:\n{[f"Name: {cookie.name} - Domain: {cookie.domain}" for cookie in self.session.cookies]}')
            if login.headers["Content-Type"] == "text/xml":
                _println("XML")
                response_xml = xmltodict.parse(login.text)['mobileresponse']
                if response_xml['@status'] == 'OK':
                    input(response_xml['@userid'])
                    self.user_id = response_xml['@userid']
                    self.batch_uid = response_xml['@batch_uid']
                    self.use_rest_api = response_xml['@use_learn_rest_api']
                    self.api_version = self.LearnAPIVersion(response_xml['@learn_version'])
                    return True, login
            else:
                _println("{}Invalid Login Response Content-Type Received: {}", Fore.RED, login.headers["Content-Type"])
        return False, login

    class BBRequestException(Exception):
        """
        An Exception is Thrown When a Error Outbound Request Error Occurs when Contacting the API
        """
        pass

    def send_get_request(self, endpoint: str, **kwargs) -> Optional[requests.Response]:
        """
        Sends a GET Request to the Endpoint Specified Using the BlackboardClient's Base Site and Handles any HTTP Errors
        that Occur

        :param endpoint: The API Path that the Client Should Take (Excluding the Base Path)
        :param kwargs: The Keyword Args are the kwargs Passed to requests.get()
        :return: Returns the Response from the Blackboard Server if it was Successful
        """
        print("Request URL: " + self.site + endpoint)
        request = None
        try:
            request = self.session.get(self.site + endpoint, cookies=self.cookie_jar, **kwargs)
            print("CODE: " + str(request.status_code))
            if request.status_code == 401:  # Unauthorised, Attempt to Log Back In
                self.login()
                request = self.session.get(self.site + endpoint, cookies=self.cookie_jar, **kwargs)
            elif request.status_code == 400 or request.status_code == 403 or request.status_code == 404:
                # Bad Request | Forbidden | Not Found
                # Most of the Time These Will Be Triggered Due to Just Spamming the API Trying to Find Stuff
                raise BlackBoardClient.RestException(request)

        # If I want to Handle These
        except (requests.exceptions.ConnectionError, requests.exceptions.HTTPError, requests.exceptions.Timeout,
                requests.exceptions.TooManyRedirects):
            raise BlackBoardClient.BBRequestException()
        except BlackBoardClient.RestException as e:
            _println(f"{Fore.RED}{str(e)}")
        return request

    def courses(self, existing_list: List[BlackBoardCourse] = None, endpoint: str = None) -> List[BlackBoardCourse]:
        """
        Attempts to get All the Courses that the BlackboardClient (User) has Access to.

        -----

        Is a Recursive Function so when called existing_list and endpoint are not Required


        :param existing_list: The List of Already Identified Courses
        :param endpoint: The Endpoint (API Path) to Send the Next Request to (due to paging)
        :return: A List Containing All the Blackboard Courses the Client Access to
        """
        if existing_list is None:
            existing_list = list()
        if endpoint is None:
            endpoint = BlackBoardEndPoints.get_user_courses(self.user_id)
        if self.use_rest_api:
            try:
                request = self.send_get_request(endpoint)
                course_data = request.json()
                if "results" in course_data:
                    for course in course_data["results"]:
                        existing_list.append(BlackBoardCourse.generate_course(self, course['courseId']))
                    if "paging" in course_data:
                        return self.courses(existing_list, course_data['paging']['nextPage'])
                    else:
                        existing_list.extend(self.additional_courses)
            except ValueError:  # JSON Response Malformed
                _println("{}[ERROR] Failed to Decode JSON Response From Endpoint: {}", Fore.RED, self.site + endpoint)
            except BlackBoardClient.BBRequestException:  # Request Error
                pass
        # Remnants of XML Implementation.
        # else:
        #     course_data = xmltodict.parse(self.session.get(
        #         self.institute.b2_url + "enrollments?v=1&f=xml&ver=4.1.2&course_type=ALL&include_grades=false").text)
        #     if course_data['mobileresponse'] and course_data['mobileresponse']['@status'] == 'OK':
        #         for course in course_data['mobileresponse']['courses']['course']:
        #             existing_list.append(BlackBoardCourseXML(self, data=course))
        #         existing_list.extend(self.additional_courses)

        # Verify Courses -- May Not Be Needed
        for course in existing_list:
            if course.id is None or course.name is None:
                existing_list.remove(course)
        return existing_list

    def add_course(self, course_id: str) -> None:
        """
        Attempts to Add an Specific Course to the Clients Additional Course List
        :param course_id: The ID of the Course that is to be Added
        """
        if course_id is None:
            raise Exception("Failed to Add Course")
        self.additional_courses.append(BlackBoardCourse.generate_course(self, course_id))

    def public_endpoint_available(self) -> bool:
        """
        Sends Request to the Blackboard Server to Test Whether the Public API is Accessible

        :return: Boolean Based on Whether the /public/ API is Accessible
        """
        return self.send_get_request("/learn/api/public/v1/system/version").ok

    def __str__(self):
        return "{}".format(self.username)

    def __repr__(self):
        return str(self)

    class LearnAPIVersion:
        """
        Represents a Blackboard LearnAPI Version

        ----

        Used to Parse and Compare the Semantic Versioning of a Server
        """

        def __init__(self, learn_version: str):
            self._raw = learn_version.split('.')
            self.major = int(self._raw[0])
            self.minor = int(self._raw[1])
            self.patch = int(self._raw[2])

        def comparable(self) -> Tuple[str]:
            """
            Generates a Tuples That Allows for Blackboard Server Versions to Be Compared

            :return: Returns a Tuple that Can Then be used to Compare Against Another LearnAPIVersion
            """
            filled = []
            for point in str(self).split("."):
                filled.append(point.zfill(8))
            return tuple(filled)

        def __repr__(self):
            return str(self)

        def __str__(self):
            return "{}.{}.{}".format(self.major, self.minor, self.patch)

        def __lt__(self, other: BlackBoardClient.LearnAPIVersion):
            return self.comparable() < other.comparable()

        def __le__(self, other: BlackBoardClient.LearnAPIVersion):
            return self.comparable() <= other.comparable()

        def __eq__(self, other: BlackBoardClient.LearnAPIVersion):
            return self.comparable() == other.comparable()

        def __ne__(self, other: BlackBoardClient.LearnAPIVersion):
            return self.comparable() != other.comparable()

        def __gt__(self, other: BlackBoardClient.LearnAPIVersion):
            return self.comparable() > other.comparable()

        def __ge__(self, other: BlackBoardClient.LearnAPIVersion):
            return self.comparable() >= other.comparable()

    class RestException(Exception):
        """
        Represents a RESTful API Exception

        -----

        Raised When the Blackboard Server API Returns a Error Status Code and Response

        """

        def __init__(self, response: requests.Response):
            self.__response = response
            try:
                self.json = response.json()
            except ValueError:
                self.json = {}
            self.status = self.json.get("status", -1)
            self.code = self.json.get("code", -1)
            self.message = self.json.get("message ", "")
            self.developer_message = self.json.get("developerMessage ", "")
            self.extra_info = self.json.get("extraInfo ", "")

        def __repr__(self):
            return str(self)

        def __str__(self):
            if not self.json:
                return self.__response
            else:
                return "REST Exception:\nPath: {}\nStatus: {}\nCode: {}\nMessage: {}\nDeveloper Message:{}\nExtra " \
                        "Info: {}".format(
                        self.__response.url, self.status, self.code, self.message, self.developer_message,
                        self.extra_info)

    def stop_threaded_downloads(self, _signal=None, _frame=None) -> None:
        """
        Shuts down the Download Queue that is Managing Threaded Downloads
        """
        _println(f"{Fore.LIGHTCYAN_EX}SIGINT Received Please Wait For The Currently Running Downloads to Complete....")
        self.thread_pool.shutdown(wait=True, cancel_futures=True)


class BlackBoardEndPoints:
    """
    A Static Helper Class that Formats the public LearnAPI Paths and Routes
    """

    @staticmethod
    def get_course_children(course_id: str) -> str:
        """
        Returns the Desired Path for a Courses Child Courses

        :param course_id: The Course ID that is to be Formatted
        :return: A String that has the required API Path to Access a Courses Child Courses
        """
        return f"/learn/api/public/v1/courses/{course_id}/children"

    @staticmethod
    def get_course(course_id: str) -> str:
        """
        Returns the Desired Path for a Course (V2 Path)

        :param course_id: The Course ID that is to be Formatted
        :return: A String that has the required API Path to Access the Provided Course
        """
        return f"/learn/api/public/v2/courses/{course_id}"

    @staticmethod
    def get_course_v1(course_id: str) -> str:
        """
        Returns the Desired Path for a Course (V1 Path)

        :param course_id: The Course ID that is to be Formatted
        :return: A String that has the required API Path to Access the Provided Course
        """
        return f"/learn/api/public/v1/courses/{course_id}"

    @staticmethod
    def get_child_course(course_id: str, child_course_id: str) -> str:
        """
        Returns the Desired Path for a Courses Child Course

        :param course_id: The Parent Course ID that is to be Formatted
        :param child_course_id: The Child Course ID that is to be Formatted
        :return: A String that has the required API Path to Access a Courses Child Course
        """
        return f"/learn/api/public/v1/courses/{course_id}/children/{child_course_id}"

    @staticmethod
    def get_user_courses(user_id: str) -> str:
        """
        Returns the Desired Path for a All of a Users Registered Courses

        :param user_id: The User ID that is to be Formatted
        :return: A String that has the required API Path to See All of a Users Registered Courses
        """
        return f"/learn/api/public/v1/users/{user_id}/courses"

    @staticmethod
    def get_user_by_username(username: str) -> str:
        """
        Returns a lists of users based on a username query string

        :param username: The Username of the user of the request
        :return: A List of User Objects that has the based on the search criteria
        """
        return f"/learn/api/public/v1/users?userName={username}"

    @staticmethod
    def get_file_attachments(course_id: str, content_id: str) -> str:
        """
        Returns the Desired Path for a Contents Attachment List

        :param course_id: The Course ID that is to be Formatted
        :param content_id: The Content ID that is to be
        :return: A String that has the required API Path to Preview the Attachments of the Provided Course and Content
        """
        return f"/learn/api/public/v1/courses/{course_id}/contents/{content_id}/attachments"

    @staticmethod
    def get_file_attachment(course_id: str, content_id: str, attachment_id: str) -> str:
        """
        Returns the Desired Path for an Attachment

        :param course_id: The Course ID that is to be Formatted
        :param content_id: The Content ID that is to be Formatted
        :param attachment_id: The Attachment ID that is to be Formatted
        :return: A String that has the required API Path to Access an Attachment
        """
        return f"/learn/api/public/v1/courses/{course_id}/contents/{content_id}/attachments/{attachment_id}"

    @staticmethod
    def get_file_attachment_download(course_id: str, content_id: str, attachment_id: str) -> str:
        """
        Returns the Desired Path for an Attachments Download Information

        :param course_id: The Course ID that is to be Formatted
        :param content_id: The Content ID that is to be Formatted
        :param attachment_id: The Attachment ID that is to be Formatted
        :return: A String that has the required API Path to Access an Attachments Download Information
        """
        return f"/learn/api/public/v1/courses/{course_id}/contents/{content_id}/attachments/{attachment_id}/download"

    @staticmethod
    def get_contents(course_id: str) -> str:
        """
        Returns the Desired Path for a Courses Contents

        :param course_id: The Course ID that is to be Formatted
        :return: A String that has the required API Path to Access a Courses Contents
        """
        return f"/learn/api/public/v1/courses/{course_id}/contents"

    @staticmethod
    def get_content(course_id: str, content_id: str) -> str:
        """
        Returns the Desired Path for a Specific Courses Content Information

        :param course_id: The Course ID that is to be Formatted
        :param content_id: The Content ID that is to be Formatted
        :return: A String that has the required API Path to Access a Specific Courses Content Information
        """
        return f"/learn/api/public/v1/courses/{course_id}/contents/{content_id}"

    @staticmethod
    def get_content_children(course_id: str, content_id: str) -> str:
        """
        Returns the Desired Path for a Contents Child Content

        :param course_id: The Course ID that is to be Formatted
        :param content_id: The Content ID that is to be Formatted
        :return: A String that has the required API Path to a Contents Child Content
        """
        return f"/learn/api/public/v1/courses/{course_id}/contents/{content_id}/children"


class BlackBoardCourse:
    """
    Represents a Blackboard Course
    """

    def __init__(self, client: BlackBoardClient, data: dict):
        """
        :param client: The Blackboard Client to Interact with this Course with
        :param data: The JSON data returned from the Learn API
        """
        self.client = client
        self._course_data = data
        self.id = self._course_data.get('id', None)
        self.uuid = self._course_data.get('uuid', None)
        self.external_id = self._course_data.get('externalId', None)
        self.data_source_id = self._course_data.get('dataSourceId', None)
        self.course_id = self._course_data.get('courseId', None)
        self.name = self._course_data.get('name', None)
        self.name_safe = re.sub('[<>:"/\\\\|?*]', '-', self.name) if self.name is not None else ''
        self.description = self._course_data.get('description', None)
        self.created = _to_date(self._course_data.get('created', None))
        self.modified = _to_date(self._course_data.get('modified', None))
        self.organization = self._course_data.get('organization', None)
        self.ultra_status = self._course_data.get('ultraStatus', None)
        self.allow_guests = self._course_data.get('allowGuests', None)
        self.closed_complete = self._course_data.get('closedComplete', None)
        self.term_id = self._course_data.get('termId', None)
        self.availability = self.Availability(self._course_data.get('available', None))
        self.enrollment = self.Enrollment(self._course_data.get('enrollment', None))
        self.locale = self.Locale(self._course_data.get('locale', None))
        self.has_children = self._course_data.get('hasChildren', None)
        self.parent_id = self._course_data.get('parentId', None)
        self.external_access_url = self._course_data.get('externalAccessUrl', None)
        self.guest_access_url = self._course_data.get('guestAccessUrl', None)
        # V1 Attributes
        self.read_only = self._course_data.get('readOnly', None)

        # Custom Attributes
        self.local_location = os.path.join(self.client.base_path, self.name_safe)
        self.active_downloads = 0

        # Manifest
        self.manifest_location = os.path.join(self.local_location, ".manifest.json")
        if self.client.use_manifest and os.path.isdir(self.local_location) and os.path.isfile(self.manifest_location):
            with open(self.manifest_location) as f:
                self.download_manifest = json.load(f)
        else:
            self.download_manifest = {}

    def __str__(self):
        return "{} ({})".format(self.name, self.id)

    def __repr__(self):
        return str(self)

    class Availability:
        """
        Represents a Blackboard Courses Availability Attributes
        """

        def __init__(self, availability_4: dict):
            if not availability_4:
                availability_4 = {}
            self.available = availability_4.get('available', None)
            self.duration = BlackBoardCourse.Duration(
                availability_4.get('duration', None))

    class Enrollment:
        """
        Represents a Blackboard Courses Enrollment Attributes
        """

        def __init__(self, enrollment_0: dict):
            if not enrollment_0:
                enrollment_0 = {}
            self.type = enrollment_0.get('type', None)
            self.start = _to_date(enrollment_0.get('start', None))
            self.end = _to_date(enrollment_0.get('end', None))
            self.access_code = enrollment_0.get('accessCode', None)

    class Locale:
        """
        Represents a Blackboard Courses Locale Attributes
        """

        def __init__(self, locale_0: dict):
            if not locale_0:
                locale_0 = {}
            self.id = locale_0.get('id', None)
            self.force = locale_0.get('force', None)

    class Duration:
        """
        Represents a Blackboard Courses Duration Attributes
        """

        def __init__(self, duration: dict):
            if not duration:
                duration = {}
            self.type = duration.get('type', None)
            self.start = _to_date(duration.get('start', None))
            self.end = _to_date(duration.get('end', None))
            self.daysOfUse = duration.get('daysOfUse', None)

    def contents(self, existing_list=None, endpoint=None) -> List[BlackBoardContent]:
        """
        Generates a List of the Contents that the Course Contains

        -----

        Is a Recursive Function so when called existing_list and endpoint are not Required


        :param existing_list: The List of the Already Identified Course Contents
        :param endpoint: The Endpoint (API Path) to Send the Next Request to (due to paging)
        :return: A List Containing All the Blackboard Content Accessible Within a Given Course
        """
        if existing_list is None:
            existing_list = list()
        if endpoint is None:
            endpoint = BlackBoardEndPoints.get_contents(self.id)
        try:
            request = self.client.send_get_request(endpoint)
            content_data = request.json()
            if "results" in content_data:
                for content in content_data["results"]:
                    existing_list.append(BlackBoardContent(self, content))
                if "paging" in content_data:
                    return self.contents(existing_list, content_data['paging']['nextPage'])
        except ValueError:  # JSON Response Malformed
            _println("{}[ERROR] Failed to Decode JSON Response From Endpoint: {}",
                     Fore.RED, self.client.site + endpoint)
        except BlackBoardClient.BBRequestException:  # Request Error
            pass

        # Verify Content
        for content in existing_list:
            if content.id is None or content.title is None:
                existing_list.remove(content)
        return existing_list

    def get_content(self, content_id: str) -> Optional[BlackBoardContent]:
        """
        Attempts to Get the Specified Content From the Course

        :param content_id: The ID of the Content Within the Course to Acquire
        :return: The Requested Blackboard Content if it Exists
        """
        return BlackBoardContent.generate_content(self, content_id)

    def download_all_attachments(self, save_location='./', threaded=False) -> None:
        """
        Enumerates Through all the Possible Content Within the Course and then Downloading All Attachments

        :param save_location: The Base Location to Save All Attachment Downloads
        :param threaded: Download The Files Across Multiple Threads
        """

        # Content Iteration Loop
        def iterate_with_path(content: BlackBoardContent, path: str) -> None:
            """
            Iterates Through the Given Content and its Child Content to Download Attachments

            :param content: The Parent Content to Search For Child Content and Attachments
            :param path: The Current Path to Save Downloads
            """
            if content.content_handler.id == "resource/x-bb-folder":
                path = os.path.join(path, content.title_safe)
            for attachment in content.attachments():
                if threaded:
                    # Will Raise DownloadQueueCancelled if downloading has been cancelled
                    attachment.thread_download(path)
                else:
                    attachment.download(path)
            if content.has_children:
                for child in content.children():
                    iterate_with_path(child, path)

        # Content Iteration Start
        contents = self.contents()
        for c in contents:
            iterate_with_path(c, os.path.join(save_location, self.name_safe))

        if not threaded:
            self.finished_course_downloads()

    def get_manifest_entry(self, attachment: BlackBoardAttachment) -> Optional[str]:
        """
        Query the Download Manifest To Check If The Associated Attachment Been Updated

        :param attachment: The Attachment to Get Manifest Data For
        :return: The ETag that was Recorded when the Attachment was Last Downloaded
        """
        return self.download_manifest.get(attachment.content.id, {}).get(attachment.id, None)

    def finished_course_downloads(self):
        """
        Writes Changes to Manifest (If Enabled) and Notifies that The Course Content has been Downloaded
        """
        _println(f"{Fore.MAGENTA}[COURSE DOWNLOADED] {self.name_safe}\n")
        # Manifest Save - Check if Directory Exists Because if it doesn't No Files Have Been Downloaded
        if self.client.use_manifest and os.path.isdir(self.local_location):
            with open(self.manifest_location, 'w+') as f:
                json.dump(self.download_manifest, f)

    @staticmethod
    def generate_course(client: BlackBoardClient, course_id: str) -> Optional[BlackBoardCourse]:
        """
        Contacts The Learn Course Endpoint and Makes a BlackboardCourse Class

        :param client: The Client to use when Generating the Provided Course
        :param course_id: The Course ID Related to the Course to Generate
        :return: The Blackboard Course Associated with The Provided Course ID
        """
        if client.api_version >= client.LearnAPIVersion("3400.8.0"):
            endpoint = BlackBoardEndPoints.get_course(course_id)
        else:
            endpoint = BlackBoardEndPoints.get_course_v1(course_id)
        try:
            response = client.send_get_request(endpoint)
            return BlackBoardCourse(client, response.json())
        except (ValueError, TypeError):  # JSON Response Malformed, None Type
            _println("{}[ERROR] Failed to Decode JSON Response From Endpoint: {}", Fore.RED, client.site + endpoint)
        except BlackBoardClient.BBRequestException:  # Request Error
            pass


class BlackBoardContent:
    """
    Represents a Piece Content Within a Blackboard Course
    """

    def __init__(self, course: BlackBoardCourse, data: dict):
        """
        :param course: The Blackboard Course that holds this Content
        :param data: The JSON data returned from the Learn API
        """
        self.course = course
        self.client = course.client
        self.__content_data = data
        self.id = self.__content_data.get('id', None)
        self.parent_id = self.__content_data.get('parentId', None)
        self.title = self.__content_data.get('title', None)
        self.title_safe = re.sub(
            '[<>:"/\\\\|?*]', '-', self.title) if self.title is not None else ''
        self.body = self.__content_data.get('body', None)
        self.description = self.__content_data.get('description', None)
        self.created = _to_date(self.__content_data.get('created', None))
        self.position = self.__content_data.get('position', None)
        self.has_children = self.__content_data.get('hasChildren', None)
        self.has_gradebook_columns = self.__content_data.get('hasGradebookColumns', None)
        self.has_associated_groups = self.__content_data.get('hasAssociatedGroups', None)
        self.availability = self.Availability(self.__content_data.get('availability', None))
        self.content_handler = self.ContentHandler(self.__content_data.get('contentHandler', None))
        self.links = [self.Link(link) for link in self.__content_data.get('links', [])]

    def __str__(self):
        return "{} ({})".format(self.title, self.id)

    def __repr__(self):
        return str(self)

    class Availability:
        """
        Represents the Blackboard Content's Availability Attributes
        """

        def __init__(self, availability_0: dict):
            if not availability_0:
                availability_0 = {}
            self.available = availability_0.get('available', None)
            self.duration = availability_0.get('allowGuests', None)
            self.duration = BlackBoardContent.AdaptiveRelease(
                availability_0.get('adaptiveRelease', None))

    class AdaptiveRelease:
        """
        Represents the Blackboard Content's Adaptive Release Attributes
        """

        def __init__(self, adaptive_release: dict):
            if not adaptive_release:
                adaptive_release = {}
            self.start = _to_date(adaptive_release.get('available', None))
            self.end = _to_date(adaptive_release.get('allowGuests', None))

    class ContentHandler:
        """
        Represents the Blackboard Content's Content Handler Attributes
        """

        def __init__(self, content_handler: dict):
            if not content_handler:
                content_handler = {}
            self.id = content_handler.get('id', None)
            self.url = content_handler.get('url', None)
            self.is_bb_page = content_handler.get('isBbPage', None)
            self.target_id = content_handler.get('targetId', None)
            self.target_type = content_handler.get('targetType', None)
            self.discussion_id = content_handler.get('discussionId', None)
            self.discussion_id = content_handler.get('discussionId', None)
            self.custom_parameters = content_handler.get('customParameters', None)
            self.file = self.BBFile(content_handler.get('file', None))
            self.assessment_id = content_handler.get('customParameters', None)
            self.grade_column_id = content_handler.get('gradeColumnId ', None)
            self.group_content = content_handler.get('groupContent ', None)

        def __str__(self):
            return "Content Type: {} - Populated Attributes: {}" \
                .format(self.id,
                        [k for k, v in self.__dict__.items() if
                         '__' not in k and 'object at' not in k and v is not None])

        def __repr__(self):
            return str(self)

        class BBFile:
            """
            Represents a Blackboard File Embedded in the Content Handler
            """

            def __init__(self, content_handler: dict):
                if not content_handler:
                    content_handler = {}
                self.upload_id = content_handler.get('uploadId', None)
                self.file_name = content_handler.get('fileName', None)
                self.mime_type = content_handler.get('mimeType', None)
                self.duplicate_file_handling = self.FileHandling(content_handler.get('duplicateFileHandling', None))

            class FileHandling:
                """
                Represents a Blackboard File Embedded in the Content's File Handling Attributes
                """

                def __init__(self, content_handler: dict):
                    if not content_handler:
                        content_handler = {}

                    self.rename = content_handler.get('Rename', None)
                    self.replace = content_handler.get('Replace', None)
                    self.throw_error = content_handler.get('ThrowError', None)

            def __str__(self):
                return "{} ({})".format(self.file_name, self.mime_type)

            def __repr__(self):
                return str(self)

    class Link:
        """
        Represents the Blackboard Content's Linking Attributes
        """

        def __init__(self, data: dict):
            self.href = data.get("href", None)
            self.rel = data.get("ref", None)
            self.title = data.get("title", None)
            self.type = data.get("type", None)

    def children(self, existing_list=None, endpoint=None) -> List[BlackBoardContent]:
        """
        Get All Child Content Associated with the current Content

        -----

        Is a Recursive Function so when called existing_list and endpoint are not Required


        :param existing_list: The List of the Already Identified Course Contents
        :param endpoint: The Endpoint (API Path) to Send the Next Request to (due to paging)
        :return: A List Containing All the Child Blackboard Content Accessible Within the Given Content
        """
        if existing_list is None:
            existing_list = list()
        if endpoint is None:
            endpoint = BlackBoardEndPoints.get_content_children(self.course.id, self.id)
        if self.has_children:
            try:
                request = self.client.send_get_request(endpoint)
                children_content = request.json()  # Can Produce Value Error
                if "results" in children_content:
                    for content in children_content["results"]:
                        existing_list.append(BlackBoardContent(self.course, content))
                    if "paging" in children_content:
                        return self.children(existing_list, children_content['paging']['nextPage'])
            except ValueError:  # JSON Response Malformed
                _println(
                    f"{Fore.RED}[ERROR] Failed to Decode JSON Response From Endpoint: {self.client.site + endpoint}")
            except BlackBoardClient.BBRequestException:  # Request Error
                pass

        # Verify Children
        for content in existing_list:
            if content.id is None or content.title is None:
                existing_list.remove(content)
        return existing_list

    def attachments(self, existing_list=None, endpoint=None) -> List[BlackBoardAttachment]:
        """
        Get All Attachments Associated with the current Content

        -----

        Is a Recursive Function so when called existing_list and endpoint are not Required


        :param existing_list: The List of the Already Identified Course Contents
        :param endpoint: The Endpoint (API Path) to Send the Next Request to (due to paging)
        :return: A List Containing All the Blackboard Attachments Accessible Within the Given Content
        """
        if existing_list is None:
            existing_list = list()
        if endpoint is None:
            endpoint = BlackBoardEndPoints.get_file_attachments(self.course.id, self.id)
        if self.content_handler.id in ("resource/x-bb-file", "resource/x-bb-document", "resource/x-bb-assignment"):
            try:
                request = self.client.send_get_request(endpoint)
                attachments = request.json()
                if "results" in attachments:
                    for content in attachments["results"]:
                        existing_list.append(BlackBoardAttachment(self, content))
                    if "paging" in attachments:
                        return self.attachments(existing_list, attachments['paging']['nextPage'])
            except ValueError:  # JSON Response Malformed
                _println("{}[ERROR] Failed to Decode JSON Response From Endpoint: {}",
                         Fore.RED, self.client.site + endpoint)
            except BlackBoardClient.BBRequestException:  # Request Error
                pass
        # Verify Attachment
        for content in existing_list:
            if content.id is None or content.file_name is None:
                existing_list.remove(content)
        return existing_list

    @staticmethod
    def generate_content(course: BlackBoardCourse, content_id: str) -> Optional[BlackBoardContent]:
        """
        Contacts The Learn Course Endpoint and Makes a BlackboardContent Class

        :param course: The Course to use when Generating the Content
        :param content_id: The Content ID Related to the Content to Generate
        :return: The Blackboard Content Associated with The Provided Content ID and Course
        """
        endpoint = BlackBoardEndPoints.get_content(course.id, content_id)
        try:
            response = course.client.send_get_request(endpoint)
            return BlackBoardContent(course, response.json())
        except (ValueError, TypeError):  # JSON Response Malformed, None Type
            _println("{}[ERROR] Failed to Decode JSON Response From Endpoint: {}",
                     Fore.RED, course.client.site + endpoint)
        except BlackBoardClient.BBRequestException:  # Request Error
            pass


class BlackBoardAttachment:
    """
    Represents an Attachment Within Blackboard Content
    """

    def __init__(self, content: BlackBoardContent, data: dict):
        """
        :param content: The Blackboard Content that the Attachment is Attached to
        :param data: The JSON data returned from the Learn API
        """
        self.id = data.get('id', None)
        self.file_name = data.get('fileName', None)
        self.file_name_safe = unquote(re.sub(
            '[<>:"/\\\\|?*]', '', self.file_name)) if self.file_name is not None else ''
        self.mime_type = data.get('mimeType', None)
        self.client = content.client
        self.course = content.course
        self.content = content

    def __str__(self):
        return "{} ({}) - {}".format(self.file_name, self.id, self.mime_type)

    def __repr__(self):
        return str(self)

    def download(self, location: str) -> None:
        """
        Downloads the Attachment File to The Specified Location

        :param location: The Location to Save the Attachment to (Is a Directory as Download Will Append the File Name)
        """
        # Just Work in Absolute Paths
        download_location = os.path.abspath(os.path.join("." if location is None else location, self.file_name_safe))
        download_directory = os.path.dirname(download_location)

        request_headers = {}
        if self.client.use_manifest and self.course.get_manifest_entry(self) is not None:
            request_headers["If-None-Match"] = self.course.download_manifest[self.content.id][self.id]

        endpoint = BlackBoardEndPoints.get_file_attachment_download(self.course.id, self.content.id, self.id)
        download = self.client.send_get_request(endpoint, allow_redirects=True, headers=request_headers)

        if download.status_code == 302:  # Redirect Already Handled By Requests
            _println(f"{Fore.CYAN}[REDIRECT]: {download.headers.get('Location', None)}")
        elif download.status_code == 304:  # No Need to Update File
            _println(f"{Fore.YELLOW}[UP TO DATE] {self.file_name_safe}\n[LOCATION] {download_directory}")
        elif download.status_code == 200:
            if not os.path.exists(download_directory):
                os.makedirs(download_directory)

            file_exists = os.path.isfile(download_location)

            if file_exists and not self.client.use_manifest:
                _println(f"{Fore.YELLOW}[UP TO DATE] {self.file_name_safe}\n[LOCATION] {download_directory}")
                return

            if file_exists and self.client.use_manifest and self.client.backup_files:
                try:
                    backup_folder = os.path.join(download_directory, "backups")
                    split_file_name = self.file_name_safe.split('.')
                    date_updated = datetime.strptime(download.headers['Last-Modified'], "%a, %d %b %Y %H:%M:%S %Z")
                    new_file_name = "{}_{}.{}".format('.'.join(split_file_name[:-1]), date_updated.strftime('%d-%m-%Y'),
                                                      split_file_name[-1])
                    backup_file = os.path.join(backup_folder, f"_{new_file_name}")
                    _println(f"{Fore.YELLOW}[BACKING UP] {self.file_name_safe}\n[LOCATION] {backup_file}")
                    if not os.path.exists(f"{backup_folder}"):
                        os.makedirs(f"{backup_folder}")
                    os.replace(download_location, backup_file)
                except OSError:
                    _println(f"{Fore.RED}[FAILED BACKUP] Failed to Backup File: {self.file_name_safe}")

            if self.content.id not in self.course.download_manifest:
                self.course.download_manifest[self.content.id] = {}

            # Possible Server Doesn't Supply ETag
            self.course.download_manifest[self.content.id][self.id] = download.headers.get("ETag", -1)

            try:
                with open(download_location, 'wb+') as file_out:
                    file_out.write(download.content)
                _println(
                    "{}[{}] {}\n[LOCATION] {}",
                    Fore.GREEN, 'UPDATED' if file_exists else 'DOWNLOADED', self.file_name_safe, download_directory)
            except OSError:
                _println(f"{Fore.RED}[FAILED TO DOWNLOAD FILE] {self.file_name_safe}")
        else:
            _println(f"{Fore.RED}[UNKNOWN STATUS CODE] {download.status_code}")

    @staticmethod
    def generate_attachment(content: BlackBoardContent, attachment_id: str) -> Optional[BlackBoardAttachment]:
        """
        Contacts The Learn Course Endpoint and Makes a BlackboardAttachment Class

        :param content: The Content to use when Generating the Attachment
        :param attachment_id: The Attachment ID Related to the Attachment to Generate
        :return: The Blackboard Attachment Associated with The Provided Content
        """
        endpoint = BlackBoardEndPoints.get_file_attachment(content.course.id, content.id, attachment_id)
        try:
            response = content.client.send_get_request(endpoint)
            return BlackBoardAttachment(content, response.json())
        except (ValueError, TypeError):  # JSON Response Malformed, None Type
            _println("{}[ERROR] Failed to Decode JSON Response From Endpoint: {}",
                     Fore.RED, content.client.site + endpoint)
        except BlackBoardClient.BBRequestException:  # Request Error
            pass

    def thread_download(self, path: str):
        """
        Starts a Download Using the Thread Pool Provided by the Client
        :param path: The Save Path for the Attachment
        """
        self.course.active_downloads += 1
        self.client.thread_pool.enqueue(self.download, self.__download_callback, path)

    def __download_callback(self, error: Optional[Exception]) -> None:
        """
        A Callback Function that is called after an Attachment has been Downloaded so the Manifest

        :param error: Provided if there was an Error During the Main Function Execution
        """

        if error is not None:
            _println(f"{Fore.RED}[FAILED TO DOWNLOAD FILE] {self.file_name_safe}\nError: {str(error)}")

        # Probably Will Spam on Faster Downloads :(
        time.sleep(1)  # I/O Block For 1 Sec to Give Time
        self.course.active_downloads -= 1
        if self.course.active_downloads < 1:
            self.course.finished_course_downloads()


class FunctionQueue:
    """
    Add Functions that are to be Executed in the Added Order
    """
    def __init__(self):
        self.queue: List[Tuple[Callable[..., None], Tuple[Any, ...], Dict[str, Any]]] = []
        self.thread: Optional[threading.Thread] = None

    def enqueue(self, fn: Callable[..., None], *args, **kwargs) -> None:
        """
        Places a Function into a Queue that is then executed in the order it was received

        :param fn: Function to Execute
        :param args: Arguments for the Provided Function
        :param kwargs: Keyword Arguments for the Provided Function
        """
        self.queue.append((fn, args, kwargs))
        if self.thread is None:
            self.thread = threading.Thread(target=self._run)
            self.thread.start()

    def _run(self) -> None:
        """
        The Worker Function that Runs Inside a Thread Executing the Received Functions
        """
        while len(self.queue) > 0:
            (fn, args, kwargs) = self.queue.pop(0)
            fn(*args, **kwargs)

        # Probably Not the best idea to wastefully spam thread creations
        # Sleep will also create some text pausing and jumping
        time.sleep(0.8)  # Wait 0.8 Seconds and if no more Functions come Exit Thread..
        if len(self.queue) > 0:
            self._run()
        self.thread = None


function_queue = FunctionQueue()


def _println(text: str, *args) -> None:
    """
    Print Function that Adds an Extra Newline and Formats a String
    :param text: The Text to Print/Format
    :param args: The Formatting Arguments
    """
    function_queue.enqueue(print, text.format(*args) + f"{Fore.RESET}\n")
    # print(text.format(*args) + f"{Fore.RESET}\n")


def _to_date(date_string) -> Optional[datetime]:
    """
    Takes a Date String and Converts it To a Datetime Value based on ISO 8601 using Either Time Zone Name or Offset
    :param date_string: The DateTime String to Convert
    :return: If Successful a datetime object
    """
    if date_string is None:
        return None
    else:
        try:
            return datetime.strptime(date_string, '%Y-%m-%dT%H:%M:%S.%f%z')
        except ValueError:
            return datetime.strptime(date_string, '%Y-%m-%dT%H:%M:%S.%fZ')


class DownloadQueue(futures.ThreadPoolExecutor):
    """
    A Download Queue to Allow For Multi-Threaded Downloads
    """

    class DownloadQueueCancelled(Exception):
        """
        An Exception is Thrown When The ThreadPoolExecutor has been Shutdown
        """
        pass

    def __init__(self, thread_count: int):
        """
        :param thread_count: The Maximum Number of Worker Threads to Spawn
        """
        super().__init__(max_workers=thread_count)

    def enqueue(self, fn: Callable[..., None], cb: Callable[[Optional[Exception]], None], *args) -> None:
        """
        Places The Provided Functions in a ThreadPool Executor

        :param fn: The Function to Execute
        :param cb: The Function to Call After Execution
        :param args: The Arguments For the Function to Execute (fn)
        """
        try:
            self.submit(DownloadQueue.__fn_with_cb, *(fn, cb, *args))
        except RuntimeError:
            raise DownloadQueue.DownloadQueueCancelled()

    @staticmethod
    def __fn_with_cb(fn: Callable[..., None], cb: Callable[[Optional[Exception]], None], *args) -> None:
        """
        The Function That is Passed into the ThreadPool and wraps the functions in a Try Except to Detect Errors

        :param fn: The Function to Execute
        :param cb: The Function to Call After Execution
        :param args: The Arguments For the Function to Execute (fn)
        """
        error = None
        try:
            fn(*args)
        except Exception as e:
            error = e
        cb(error)


def get_cookies(learn_domain: str, default_browser: Optional[str] = None) -> CookieJar:
    """
    Attempts to get a Users Login Session from a Browser
    """
    regex = re.compile("https?://(.*)")
    learn_domain = regex.search(learn_domain).group(1)
    print(learn_domain)
    browsers = {
        "Chrome": browser_cookie3.chrome, 
        "Firefox": browser_cookie3.firefox,
        "Edge": browser_cookie3.edge,
        "Opera": browser_cookie3.opera,
        "Chromium": browser_cookie3.chromium,
        "Unknown": None
    }

    def get_cookies_from_browser(browser_name: str, browser_fn: Callable[..., CookieJar]):
        try:
            _println("Attempting to Grab Cookies from: {}", browser_name)
            ret = browser_fn() #domain_name=learn_domain 
            _println("Grabbed Cookies from: {}", browser_name)
            return ret
        except Exception:
            _println("Failed to Grab Cookies for Browser: {}", browser_name)

    if default_browser is not None:
        selection = default_browser
    else:
        from main import navigation
        selection = navigation([*browsers], title="Select a Browser to Pull Your Cookies from")
    
    if selection is None or browsers[selection] is None:
        for browser_name_, browser_func in browsers.items():
            if browser_func is None:
                continue
            
            cookies = get_cookies_from_browser(browser_name_, browser_func)
            if cookies is not None:
                return cookies
    else:
        return get_cookies_from_browser(selection, browsers[selection])
