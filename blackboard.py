import os
import re
import requests
from xml.etree import ElementTree
import json
import datetime

class BlackBoardClient:
    def __init__(self, **kwargs):
        self.username = kwargs.get('username', None)
        self.__password = kwargs.get('password', None)
        self.site = kwargs.get('site', None)
        self.session = requests.Session()
        self.user_id = None
        self.batch_uid = None
        if self.username is None or self.__password is None or self.site is None:
            raise Exception("Missing Username and/or Password and/or Site")

    # XML
    def login(self):
        login = self.session.post(
            self.site + "/webapps/Bb-mobile-bb_bb60/sslUserLogin?v=2&f=xml&ver=4.1.2",
            data={'username': self.username, 'password': self.__password})
        if login.status_code != 200:
            raise Exception("Unable to Login Using Mobile Route")
        else:
            parsed_xml = ElementTree.ElementTree(ElementTree.fromstring(login.text)).getroot()
            self.user_id = parsed_xml.attrib["userid"]
            self.batch_uid = parsed_xml.attrib["batch_uid"]

    def courses(self):
        courses = self.session.get(self.site + "/learn/api/public/v1/users/{}/courses".format(self.user_id)).json()
        if "results" in courses:
            return [BlackBoardCourse(self, course["courseId"]) for course in courses["results"]]
        return []


class BlackBoardEndPoints:
    @staticmethod
    def get_course_children(course_id: str):
        return "/learn/api/public/v1/courses/{}/children".format(course_id)

    @staticmethod
    def get_course(course_id: str):
        return "/learn/api/public/v2/courses/{}".format(course_id)

    @staticmethod
    def get_course_v1(course_id: str):
        return "/learn/api/public/v1/courses/{}".format(course_id)

    @staticmethod
    def get_child_course(course_id: str, child_course_id: str):
        return "/learn/api/public/v1/courses/{}/children/{}".format(course_id, child_course_id)

    @staticmethod
    def get_user_courses(user_id: str):
        return "/learn/api/public/v1/users/{}/courses".format(user_id)

    @staticmethod
    def get_file_attachments(course_id: str, content_id: str):
        return "/learn/api/public/v1/courses/{}/contents/{}/attachments".format(course_id, content_id)

    @staticmethod
    def get_file_attachment(course_id: str, content_id: str, attachment_id: str):
        return "/learn/api/public/v1/courses/{}/contents/{}/attachments/{}".format(course_id, content_id, attachment_id)

    @staticmethod
    def get_file_attachment_download(course_id: str, content_id: str, attachment_id: str):
        return "/learn/api/public/v1/courses/{}/contents/{}/attachments/{}/download".format(course_id, content_id,
                                                                                            attachment_id)

    @staticmethod
    def get_contents(course_id: str):
        return "/learn/api/public/v1/courses/{}/contents".format(course_id)

    @staticmethod
    def get_content(course_id: str, content_id: str):
        return "/learn/api/public/v1/courses/{}/contents/{}".format(course_id, content_id)

    @staticmethod
    def get_content_children(course_id: str, content_id: str):
        return "/learn/api/public/v1/courses/{}/contents/{}/children".format(course_id, content_id)


class BlackBoardCourse:
    def __init__(self, client: BlackBoardClient, course_id: str):
        self._client = client
        self._course_data = client.session.get(client.site + BlackBoardEndPoints.get_course(course_id)).json()
        self.id = self.request_data('id')
        self.uuid = self.request_data('uuid')
        self.external_id = self.request_data('externalId')
        self.data_source_id = self.request_data('dataSourceId')
        self.course_id = self.request_data('courseId')
        self.name = self.request_data('name')
        self.name_safe = re.sub('[<>:"/\\|?*]', '-', self.name)
        self.description = self.request_data('description')
        self.created = _to_date(self.request_data('created'))
        self.modified = _to_date(self.request_data('modified'))
        self.organization = self.request_data('organization')
        self.ultra_status = self.request_data('ultraStatus')
        self.allow_guests = self.request_data('allowGuests')
        self.closed_complete = self.request_data('closedComplete')
        self.term_id = self.request_data('termId')
        self.availability = self.Availability(self.request_data('available'))
        self.enrollment = self.Enrollment(self.request_data('enrollment'))
        self.locale = self.Locale(self.request_data('locale'))
        self.has_children = self.request_data('hasChildren')
        self.parent_id = self.request_data('parentId')
        self.external_access_url = self.request_data('externalAccessUrl')
        self.guest_access_url = self.request_data('guestAccessUrl')

    def __str__(self):
        return "{} ({})".format(self.name, self.id)

    def __repr__(self):
        return str(self)

    class Availability:
        def __init__(self, availability_4: dict):
            if not availability_4:
                availability_4 = {}
            self.available = availability_4.get('available', None)
            self.duration = BlackBoardCourse.Duration(availability_4.get('duration', None))

    class Enrollment:
        def __init__(self, enrollment_0: dict):
            if not enrollment_0:
                enrollment_0 = {}
            self.type = enrollment_0.get('type', None)
            self.start = _to_date(enrollment_0.get('start', None))
            self.end = _to_date(enrollment_0.get('end', None))
            self.access_code = enrollment_0.get('accessCode', None)

    class Locale:
        def __init__(self, locale_0: dict):
            if not locale_0:
                locale_0 = {}
            self.id = locale_0.get('id', None)
            self.force = locale_0.get('force', None)

    class Duration:
        def __init__(self, duration: dict):
            if not duration:
                duration = {}
            self.type = duration.get('type', None)
            self.start = _to_date(duration.get('start', None))
            self.end = _to_date(duration.get('end', None))
            self.daysOfUse = duration.get('daysOfUse', None)

    def request_data(self, key, specific_object: dict = None):
        if specific_object is None:
            return self._course_data.get(key, None)
        else:
            return specific_object.get(key, None)

    def contents(self):
        content_data = self._client.session.get(self._client.site + BlackBoardEndPoints.get_contents(self.id)).json()
        if "results" in content_data:
            return [BlackBoardContent(self, json=content) for content in content_data["results"]]
        return []

    def download_all_attachments(self, save_location='./'):
        # Content Iteration Loop
        def iterate_with_path(content, path=None):
            if path is None:
                path = './{}'.format(self.name_safe)
            if content.content_handler.id == "resource/x-bb-folder":
                path += ("/" + content.title_safe)
            for attachment in content.attachments():
                attachment.download(path)
            if content.has_children:
                for child in content.children():
                    iterate_with_path(child, path)

        # Content Iteration Start
        for c in self.contents():
            iterate_with_path(c, "{}/{}".format(save_location, self.name_safe))
        print("Downloaded All Attachments For Course: {}".format(self.name))


class BlackBoardContent:
    def __init__(self, course: BlackBoardCourse, **kwargs):
        self._course = course
        self._client = course._client
        self.__content_data = {}
        if "json" in kwargs:
            self.__content_data = kwargs.get('json', None)
        elif 'course_id' in kwargs and 'content_id' in kwargs:
            content_data = self._client.session.get(
                self._client.site + BlackBoardEndPoints.get_content(kwargs['course_id'], kwargs['content_id'])).json()
            if 'results' in content_data:
                self.__content_data = content_data['results']
            else:
                raise Exception("No Content")
        self.id = self.request_data('id')
        self.parentId = self.request_data('parentId')
        self.title = self.request_data('title')
        self.title_safe = re.sub('[<>:"/\\|?*]', '-', self.title)
        self.body = self.request_data('body')
        self.description = self.request_data('description')
        self.created = _to_date(self.request_data('created'))
        self.position = self.request_data('position')
        self.has_children = self.request_data('hasChildren')
        self.has_gradebook_columns = self.request_data('hasGradebookColumns')
        self.has_associated_groups = self.request_data('hasAssociatedGroups')
        self.availability = self.Availability(self.request_data('availability'))  # Class
        self.content_handler = self.ContentHandler(self.request_data('contentHandler'))  # Class

    def __str__(self):
        return "{} ({})".format(self.title, self.id)

    def __repr__(self):
        return str(self)

    class Availability:
        def __init__(self, availability_0: dict):
            if not availability_0:
                availability_0 = {}
            self.available = availability_0.get('available', None)
            self.duration = availability_0.get('allowGuests', None)
            self.duration = BlackBoardContent.AdaptiveRelease(availability_0.get('adaptiveRelease', None))

    class AdaptiveRelease:
        def __init__(self, adaptive_release: dict):
            if not adaptive_release:
                adaptive_release = {}
            self.start = _to_date(adaptive_release.get('available', None))
            self.end = _to_date(adaptive_release.get('allowGuests', None))

    class ContentHandler:
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
            def __init__(self, content_handler: dict):
                if not content_handler:
                    content_handler = {}
                self.upload_id = content_handler.get('uploadId', None)
                self.file_name = content_handler.get('fileName', None)
                self.mime_type = content_handler.get('mimeType', None)
                self.duplicate_file_handling = self.FileHandling(content_handler.get('duplicateFileHandling', None))

            class FileHandling:
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

    def request_data(self, key, specific_object: dict = None):
        if specific_object is None:
            return self.__content_data.get(key, None)
        else:
            return specific_object.get(key, None)

    def children(self):
        if self.has_children:
            children_content = self._client.session.get(
                self._client.site + BlackBoardEndPoints.get_content_children(self._course.id, self.id)).json()
            if "results" in children_content:
                return [BlackBoardContent(self._course, json=content) for content in children_content["results"]]
        return []

    def attachments(self):
        if self.content_handler.id in ("resource/x-bb-file", "resource/x-bb-document", "resource/x-bb-assignment"):
            attachments = self._client.session.get(
                self._client.site + BlackBoardEndPoints.get_file_attachments(self._course.id, self.id)).json()
            if "results" in attachments:
                return [BlackBoardAttachment(self, content) for content in attachments["results"]]
        return []

    @staticmethod
    def content_type(content_handler):
        return {
            'resource/x-bb-document': 1,
            'resource/x-bb-externallink': 2,
            'resource/x-bb-folder': 3,
            'resource/x-bb-courselink': 4,
            'resource/x-bb-forumlink': 5,
            'resource/x-bb-blti-link': 6,
            'resource/x-bb-file': 7,
            'resource/x-bb-asmt-test-link': 8,
            'resource/x-bb-assignment': 9
        }.get(content_handler["id"], None)


class BlackBoardAttachment:
    def __init__(self, content: BlackBoardContent, file_attachment: dict):
        self.id = file_attachment.get('id', None)
        self.file_name = file_attachment.get('fileName', None)
        self.mime_type = file_attachment.get('mimeType', None)
        self._client = content._client
        self._course = content._course
        self._content = content

    def __str__(self):
        return "{} ({}) - {}".format(self.file_name, self.id, self.mime_type)

    def __repr__(self):
        return str(self)

    def download(self, location=None):
        download_location = ("./{}" if location is None else location + "/{}").format(self.file_name)
        download = self._client.session.get(
            self._client.site + BlackBoardEndPoints.get_file_attachment_download(self._course.id, self._content.id,
                                                                                 self.id))
        if download.status_code == 302:
            print("File Located at: {}".format(download.headers.get("Location", "")))
        elif download.status_code == 200:
            if not os.path.exists(location):
                os.makedirs(location)
            if os.path.isfile(download_location):
                print("File Exists No Download..")
                return
            with open(download_location, 'wb') as file_out:
                file_out.write(download.content)
            print("Downloaded: {}\nto: {}\n".format(self.file_name, location))


def _to_date(date_string):
    return None if date_string is None else datetime.datetime.strptime(date_string, '%Y-%m-%dT%H:%M:%S.%f%z')
