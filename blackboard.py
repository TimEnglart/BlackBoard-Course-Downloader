import os
import re
import requests
import datetime
import xmltodict


# Thanks to: https://github.com/hako/blackboard-dl for Mobile BB XML Locations

# TODO: Use Similar Parameters Layouts for All Classes
# TODO: Add Institute Property to Client Class

class BlackBoardInstitute:
    def __init__(self, **kwargs):
        # if 'query' in kwargs:  # Use query
        # self._institute_data = BlackBoardInstitute.find(kwargs['query'])
        if 'data' in kwargs:  # pass Full Data in
            self._institute_data = kwargs['data']
        elif 'query' in kwargs:
            self._institute_data = self.find(kwargs['query'])
        else:
            # raise Exception("No Institute Data Provided")
            self._institute_data = {}

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
    def find(query):
        xml = xmltodict.parse(requests.get("https://mlcs.medu.com/api/b2_registration/match_schools/?",
                                           params={
                                               "q": query,
                                               "language": "en-GB",
                                               "platform": "android",
                                               "device_name": "Android",
                                               "carrier_code": "1337",
                                               "carrier_name": "LEET",
                                           }).text)
        if xml['data'] is not None:
            if type(xml['data']['s']) is list:
                return [BlackBoardInstitute(data=institute) for institute in xml['data']['s']]
            else:
                return [BlackBoardInstitute(data=xml['data']['s'])]
        return []


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

        self.institute = kwargs.get('institute', BlackBoardInstitute())
        self.use_rest_api = True  # Can/Cannot Use The Learn Rest API
        self.api_version = self.LearnAPIVersion("0.0.0")

    # XML
    def login(self):
        if self.institute is not None:
            login_endpoint = self.site + "/webapps/Bb-mobile-bb_bb60/"
        else:
            login_endpoint = self.institute.b2_url  # ?v=2&f=xml&ver=4.1.2

        login = self.session.post(
            login_endpoint + "sslUserLogin",
            data={'username': self.username, 'password': self.__password})
        if login.status_code == 200:
            response_xml = xmltodict.parse(login.text)['mobileresponse']
            if response_xml['@status'] == 'OK':
                self.user_id = response_xml['@userid']
                self.batch_uid = response_xml['@batch_uid']
                self.use_rest_api = response_xml['@use_learn_rest_api']
                self.api_version = self.LearnAPIVersion(response_xml['@learn_version'])
                return True
        return False

    def courses(self, existing_list=None, endpoint=None):
        if existing_list is None:
            existing_list = list()
        if endpoint is None:
            endpoint = BlackBoardEndPoints.get_user_courses(self.user_id)
        if self.use_rest_api:
            course_data = self.session.get(self.site + endpoint).json()
            if "results" in course_data:
                for course in course_data["results"]:
                    existing_list.append(BlackBoardCourse(self, course["courseId"]))
                if "paging" in course_data:
                    return self.courses(existing_list, course_data['paging']['nextPage'])
        else:
            course_data = xmltodict.parse(self.session.get(
                self.institute.b2_url + "enrollments?v=1&f=xml&ver=4.1.2&course_type=ALL&include_grades=false").text)
            if course_data['mobileresponse'] and course_data['mobileresponse']['@status'] == 'OK':
                for course in course_data['mobileresponse']['courses']['course']:
                    existing_list.append(BlackBoardCourseXML(self, data=course))

        # Verify Courses
        for course in existing_list:
            if course.id is None:
                existing_list.remove(course)
        return existing_list

    def __str__(self):
        return "{}".format(self.username)

    def __repr__(self):
        return str(self)

    class LearnAPIVersion:
        def __init__(self, learn_version: str):
            self._raw = learn_version.split('.')
            self.major = int(self._raw[0])
            self.minor = int(self._raw[1])
            self.patch = int(self._raw[2])

        def _comparable(self):
            filled = []
            for point in str(self).split("."):
                filled.append(point.zfill(8))
            return tuple(filled)

        def __str__(self):
            return "{}.{}.{}".format(self.major, self.minor, self.patch)

        def __lt__(self, other):
            return self._comparable() < other._comparable()

        def __le__(self, other):
            return self._comparable() <= other._comparable()

        def __eq__(self, other):
            return self._comparable() == other._comparable()

        def __ne__(self, other):
            return self._comparable() != other._comparable()

        def __gt__(self, other):
            return self._comparable() > other._comparable()

        def __ge__(self, other):
            return self._comparable() >= other._comparable()


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
        self.client = client
        contact_endpoint = client.site + (BlackBoardEndPoints.get_course(course_id) if
                                          client.api_version >= client.LearnAPIVersion("3400.8.0")
                                          else BlackBoardEndPoints.get_course_v1(course_id))
        print(contact_endpoint)
        self._course_data = client.session.get(contact_endpoint).json()
        self.id = self.request_data('id')
        self.uuid = self.request_data('uuid')
        self.external_id = self.request_data('externalId')
        self.data_source_id = self.request_data('dataSourceId')
        self.course_id = self.request_data('courseId')
        self.name = self.request_data('name')
        self.name_safe = re.sub('[<>:"/\\|?*]', '-', self.name) if self.name is not None else ''
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

        # V1 Attributes
        self.read_only = self.request_data('readOnly')

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
        content_data = self.client.session.get(self.client.site + BlackBoardEndPoints.get_contents(self.id)).json()
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
        self.course = course
        self.client = course.client
        self.__content_data = {}
        if "json" in kwargs:
            self.__content_data = kwargs.get('json', None)
        elif 'course_id' in kwargs and 'content_id' in kwargs:
            content_data = self.client.session.get(
                self.client.site + BlackBoardEndPoints.get_content(kwargs['course_id'], kwargs['content_id'])).json()
            # Sends No results bs as its just content for 1 Item
            self.__content_data = content_data
        self.id = self.request_data('id')
        self.parent_id = self.request_data('parentId')
        self.title = self.request_data('title')
        self.title_safe = re.sub('[<>:"/\\|?*]', '-', self.title) if self.title is not None else ''
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
            children_content = self.client.session.get(
                self.client.site + BlackBoardEndPoints.get_content_children(self.course.id, self.id)).json()
            if "results" in children_content:
                return [BlackBoardContent(self.course, json=content) for content in children_content["results"]]
        return []

    def attachments(self):
        if self.content_handler.id in ("resource/x-bb-file", "resource/x-bb-document", "resource/x-bb-assignment"):
            attachments = self.client.session.get(
                self.client.site + BlackBoardEndPoints.get_file_attachments(self.course.id, self.id)).json()
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
        self.client = content.client
        self.course = content.course
        self.content = content

    def __str__(self):
        return "{} ({}) - {}".format(self.file_name, self.id, self.mime_type)

    def __repr__(self):
        return str(self)

    def download(self, location=None, **kwargs):
        download_location = ("./{}" if location is None else location + "/{}").format(self.file_name)
        download = self.client.session.get(
            self.client.site + BlackBoardEndPoints.get_file_attachment_download(self.course.id, self.content.id,
                                                                                self.id))
        if download.status_code == 302:
            print("File Located at: {}".format(download.headers.get("Location", "")))
            # Navigate to Location
            # TODO: Add Redirect Navigation
        elif download.status_code == 200:
            if not os.path.exists(location):
                os.makedirs(location)
            if os.path.isfile(download_location):
                # Check if Overwrite
                print("File Exists No Download..")
                # TODO: Make Manifest Option
                return
            with open(download_location, 'wb') as file_out:
                file_out.write(download.content)
            print("Downloaded: {}\nto: {}\n".format(self.file_name, location))


def _to_date(date_string):
    return None if date_string is None else datetime.datetime.strptime(date_string, '%Y-%m-%dT%H:%M:%S.%f%z')


# XML Black Board Mobile Endpoint Support
# Emulate Above Classes
# TODO: Refactor XML Classes When Finished. & Refactor Entire Module


class BlackBoardCourseXML:
    def __init__(self, client: BlackBoardClient, **kwargs):
        self.client = client
        if 'data' in kwargs:
            self._course_data = kwargs['data']
        if self._course_data is None:
            self._course_data = dict()
        self.bbid = self._course_data.get('@bbid', None)
        self.name = self._course_data.get('@name', None)
        self.course_id = self._course_data.get('@courseid', None)
        self.role = self._course_data.get('@role', None)
        self.is_available = self._course_data.get('@isAvail', None)
        self.locale = self._course_data.get('@locale', None)
        self.ultra_status = self._course_data.get('@ultraStatus', None)
        self.last_access_date = self._course_data.get('@lastAccessDate', None)
        self.enrollment_date = self._course_data.get('@enrollmentdate', None)
        self.role_identifier = self._course_data.get('@roleIdentifier', None)
        self.start_date_duration = self._course_data.get('@startDateDuration', None)
        self.end_date_duration = self._course_data.get('@endDateDuration', None)
        self.duration_type = self._course_data.get('@durationType', None)
        self.days_from_the_date_of_enrollment = self._course_data.get('@daysFromTheDateOfEnrollment', None)

    def __str__(self):
        return "{} ({})".format(self.name, self.bbid)

    def __repr__(self):
        return str(self)

    def contents(self):
        content_data = xmltodict.parse(self.client.session.get(
            self.client.institute.b2_url + "courseMap?course_id=" + self.bbid).text)
        if content_data['mobileresponse'] and content_data['mobileresponse']['@status'] == 'OK':
            return [BlackBoardContentXML(self, data=content)
                    for content in content_data['mobileresponse']['map']['map-item']]
        return []

    def download_all_attachments(self, save_location='./'):
        # Content Iteration Loop
        def iterate_with_path(content: BlackBoardContentXML, path=None):
            if path is None:
                path = './{}'.format(self.name)
            if content.link_type == "resource/x-bb-folder":
                path += ("/" + content.name)
            for attachment in content.get_attachments():
                print("Would Download: {}".format(str(attachment["@name"])))
                # attachment.download(path)
            if content.children is not None:
                for child in content.get_children():
                    iterate_with_path(child, path)

        # Content Iteration Start
        for c in self.contents():
            iterate_with_path(c, "{}/{}".format(save_location, self.name))
        print("Downloaded All Attachments For Course: {}".format(self.name))


class BlackBoardContentXML:
    def __init__(self, course, **kwargs):
        self.course = course
        self.client = course.client
        if 'data' in kwargs:
            self._content_data = kwargs['data']
        else:
            self._content_data = dict()

        # TODO: Either Split into Multiple More Explicit Classes or Keep Clumped
        self.name = self._content_data.get('@name', None)
        self.view_url = self._content_data.get('@viewurl', None)
        self.is_available = self._content_data.get('@isAvail', None)
        self.link_type = self._content_data.get('@linktype', None)
        self.link_target = self._content_data.get('@linktarget', None)
        self.is_folder = self._content_data.get('@isfolder', None)
        self.new = self._content_data.get('@new', None)
        self.unread_items = self._content_data.get('@unreadItems', None)
        self.unread_key = self._content_data.get('@unreadKey', None)
        self.can_mark_as_read = self._content_data.get('@canMarkAsRead', None)
        self.content_id = self._content_data.get('@contentid', None)
        self.can_post_content_item = self._content_data.get('@canpostcontentitem', None)
        self.can_attach_files = self._content_data.get('@canattachfiles.2.5', None)
        self.date_modified = self._content_data.get('@datemodified', None)
        self.created_date = self._content_data.get('@createdDate', None)
        self.children = self._content_data.get('children', None)
        # self.map_item = self._content_data.get('map-item', None)
        self.description = self._content_data.get('description', None)

        # object containing attachment object
        self.attachments = self._content_data.get('attachments', None)

        # List or dictonary depndding on number of items. represents attachment object
        # self.attachment = self._content_data.get('attachment', None)

        # Attachment Info
        self.url = self._content_data.get('@url', None)
        self.link_label = self._content_data.get('@linkLabel', None)
        self.modified_date = self._content_data.get('@modifiedDate', None)

        # probably Assignment
        self.due_date = self._content_data.get('@dueDate', None)
        self.due_today = self._content_data.get('@dueToday', None)
        self.past_due = self._content_data.get('@pastDue', None)
        self.due_tomorrow = self._content_data.get('@dueTomorrow', None)
        self.due_after_tomorrow = self._content_data.get('@dueAfterTomorrow', None)
        self.submission_number = self._content_data.get('@submissionNumber', None)
        self.max_number_of_submission = self._content_data.get('@maxNumberOfSubmission', None)
        self.items_due_today = self._content_data.get('@itemsDueToday', None)
        self.items_past_due = self._content_data.get('@itemsPastDue', None)
        self.total_items = self._content_data.get('@totalItems', None)
        self.linked_folder = self._content_data.get('@linkedFolder', None)
        self.type = self._content_data.get('@type', None)
        self.assessment_type = self._content_data.get('@assessment_type', None)
        self.is_assessment_mobile_friendly = self._content_data.get('@is_assessment_mobile_friendly', None)

    def __str__(self):
        return "{} ({})".format(self.name, self.content_id)

    def __repr__(self):
        return str(self)

    def get_children(self):
        if self.children is not None:
            # print(type(self.children["map-item"]))
            if type(self.children["map-item"]) is list:
                return [BlackBoardContentXML(self.course, data=content) for content in self.children["map-item"]]
            elif type(self.children["map-item"]) is dict:
                return BlackBoardContentXML(self.course, data=self.children["map-item"])
        return []

    # TODO: Figure Out if I Want Separate Attachment Class Like With API
    def get_attachments(self):
        if self.link_type in ("resource/x-bb-file", "resource/x-bb-document", "resource/x-bb-assignment"):
            if self.attachments is not None:
                if type(self.attachments['attachment']) is list:
                    return [BlackBoardAttachmentXML(self, content) for content in self.attachments['attachment']]
                elif type(self.attachments['attachment']) is dict:
                    return BlackBoardAttachmentXML(self, self.attachments['attachment'])
        return []


class BlackBoardAttachmentXML:
    def __init__(self, content, attachment_data):
        self.content = content
        self.course = content.course
        self.client = content.course.client
        self.__attachment_data = attachment_data
        self.name = attachment_data['@name']
        self.url = attachment_data['@url']
        self.link_label = attachment_data['@linkLable']
        self.modified_date = attachment_data['@modifiedDate']

    def __str__(self):
        return "{}".format(self.link_label)

    def __repr__(self):
        return str(self)

    def download(self, location=None, **kwargs):
        download_location = ("./{}" if location is None else location + "/{}").format(self.link_label)
        download = self.client.session.get(self.client.institute.b2_url + self.url)
        if download.status_code == 302:
            print("File Located at: {}".format(download.headers.get("Location", "")))
            # Navigate to Location
            # TODO: Add Redirect Navigation
        elif download.status_code == 200:
            if not os.path.exists(location):
                os.makedirs(location)
            if os.path.isfile(download_location):
                # Check if Overwrite
                print("File Exists No Download..")
                # TODO: Make Manifest Option
                return
            with open(download_location, 'wb') as file_out:
                file_out.write(download.content)
            print("Downloaded: {}\nto: {}\n".format(self.link_label, location))
