#
# CURRENTLY SEPERATED AND NOT WORKING
#

# XML Black Board Mobile Endpoint Support
# Emulate Above Classes
# TODO: Refactor XML Classes When Finished. & Refactor Entire Module

import xmltodict

class BlackBoardCourseXML:
    """

    """
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
        self.start_date_duration = self._course_data.get(
            '@startDateDuration', None)
        self.end_date_duration = self._course_data.get(
            '@endDateDuration', None)
        self.duration_type = self._course_data.get('@durationType', None)
        self.days_from_the_date_of_enrollment = self._course_data.get(
            '@daysFromTheDateOfEnrollment', None)

    def __str__(self):
        return "{} ({})".format(self.name, self.bbid)

    def __repr__(self):
        return str(self)

    def contents(self):
        """

        :return:
        """
        content_data = xmltodict.parse(self.client.session.get(
            self.client.institute.b2_url + "courseMap?course_id=" + self.bbid).text)
        if content_data['mobileresponse'] and content_data['mobileresponse']['@status'] == 'OK':
            return [BlackBoardContentXML(self, data=content)
                    for content in content_data['mobileresponse']['map']['map-item']]
        return []

    def download_all_attachments(self, save_location='./'):
        """

        :param save_location:
        """
        # Content Iteration Loop
        def iterate_with_path(content: BlackBoardContentXML, path=None):
            """

            :param content:
            :param path:
            """
            if path is None:
                path = './{}'.format(self.name)
            if content.link_type == "resource/x-bb-folder":
                path += ("/" + content.name)
            for attachment in content.get_attachments():
                attachment.download(path)
            if content.children is not None:
                for child in content.get_children():
                    iterate_with_path(child, path)

        # Content Iteration Start
        for c in self.contents():
            iterate_with_path(c, "{}/{}".format(save_location, self.name))
        _println("Downloaded All Attachments For Course: {}".format(self.name))


class BlackBoardContentXML:
    """

    """
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
        self.can_post_content_item = self._content_data.get(
            '@canpostcontentitem', None)
        self.can_attach_files = self._content_data.get(
            '@canattachfiles.2.5', None)
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
        self.due_after_tomorrow = self._content_data.get(
            '@dueAfterTomorrow', None)
        self.submission_number = self._content_data.get(
            '@submissionNumber', None)
        self.max_number_of_submission = self._content_data.get(
            '@maxNumberOfSubmission', None)
        self.items_due_today = self._content_data.get('@itemsDueToday', None)
        self.items_past_due = self._content_data.get('@itemsPastDue', None)
        self.total_items = self._content_data.get('@totalItems', None)
        self.linked_folder = self._content_data.get('@linkedFolder', None)
        self.type = self._content_data.get('@type', None)
        self.assessment_type = self._content_data.get('@assessment_type', None)
        self.is_assessment_mobile_friendly = self._content_data.get(
            '@is_assessment_mobile_friendly', None)

    def __str__(self):
        return "{} ({})".format(self.name, self.content_id)

    def __repr__(self):
        return str(self)

    def get_children(self):
        """

        :return:
        """
        if self.children is not None:
            # _println(type(self.children["map-item"]))
            if type(self.children["map-item"]) is list:
                return [BlackBoardContentXML(self.course, data=content) for content in self.children["map-item"]]
            elif type(self.children["map-item"]) is dict:
                return [BlackBoardContentXML(self.course, data=self.children["map-item"])]
        return []

    # TODO: Figure Out if I Want Separate Attachment Class Like With API
    def get_attachments(self):
        """

        :return:
        """
        if self.link_type in ("resource/x-bb-file", "resource/x-bb-document", "resource/x-bb-assignment"):
            if self.attachments is not None:
                if type(self.attachments['attachment']) is list:
                    return [BlackBoardAttachmentXML(self, content) for content in self.attachments['attachment']]
                elif type(self.attachments['attachment']) is dict:
                    return [BlackBoardAttachmentXML(self, self.attachments['attachment'])]
        return []


class BlackBoardAttachmentXML:
    """

    """
    def __init__(self, content, attachment_data):
        self.content = content
        self.course = content.course
        self.client = content.course.client
        self.__attachment_data = attachment_data
        self.name = attachment_data['@name']
        self.url = attachment_data['@url']
        self.link_label = attachment_data['@linkLabel']
        self.link_label_safe = re.sub(
            '[<>:"/\\|?*]', '', self.link_label) if self.link_label is not None else ''
        self.modified_date = attachment_data['@modifiedDate']

    def __str__(self):
        return "{}".format(self.link_label)

    def __repr__(self):
        return str(self)

    def download(self, location=None, **kwargs):
        """

        :param location:
        :param kwargs:
        :return:
        """
        download_location = (
            "./{}" if location is None else location + "/{}").format(self.link_label_safe)
        download = self.client.session.get(
            self.client.institute.display_lms_host + self.url)
        if download.status_code == 302:
            _println("File Located at: {}".format(
                download.headers.get("Location", "")))
            # Navigate to Location
            # TODO: Add Redirect Navigation
        elif download.status_code == 200:
            if not os.path.exists(location):
                os.makedirs(location)
            if os.path.isfile(download_location):
                # Check if Overwrite
                _println("File Exists No Download..")
                # TODO: Make Manifest Option
                return
            try:
                with open(download_location, 'wb') as file_out:
                    file_out.write(download.content)
                _println("Downloaded: {}\nto: {}\n".format(
                    self.link_label_safe, location))
            except FileNotFoundError:
                _println(f"{self.link_label_safe} @ {location} NOT FOUND\n\n")