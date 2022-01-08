NEW_FEATURE_ISSUE_TYPES = ['Story', 'Change Request']
PRIMARY_ISSUE_TYPES = ['Story', 'Change Request', 'Bug', 'Test Plan']
SUB_ISSUE_TYPES = ['Sprint Bug', 'Sprint Task', 'Sub Test Execution']
TEST_ISSUE_TYPES = ['Test Execution', 'Test Case']
DONE_ISSUE_STATUSES = ['Done', 'Resolved', 'Fixed', 'Closed']


class JiraIssue():
    id = ''
    parent_id = ''
    key = ''
    type = ''
    status = ''
    resolution_date = ''
    story_point = 0
    logged_time_dev = 0
    logged_time_test = 0
    sub_issues = []
    work_logs = []
    contributors = {}
    main_contributor = ''

    def __init__(self):
        self.sub_issues = []
        self.work_logs = []
        self.contributors = {}

    def is_primary(self):
        return self.type in PRIMARY_ISSUE_TYPES

    def load(self, data):
        self.id = data['id']
        self.key = data['key']
        self.type = data['fields']['issuetype']['name']
        self.status = data['fields']['status']['name']
        self.work_logs = data['fields']['worklog']['worklogs']

        if self.is_primary():
            self.resolution_date = data['fields']['resolutiondate']
            self.story_point = (0 if data['fields']['customfield_10026'] is None
                                else data['fields']['customfield_10026'])
        else:
            self.parent_id = data['fields']['parent']['id']

    def init_parent_issue(self, issue):
        self.id = issue.parent_id
        self.sub_issues = [issue]


class SprintSummary():
    id = 0
    name = ''
    committed_point = 0
    finished_point = 0
    fixed_bug_count = 0
    dev_bug_count = 0
    new_feature_story_point = 0
    logged_time_total = 0
    logged_time_new_feature = 0
    logged_time_dev_bug = 0
    logged_time_existing_bug = 0
    logged_time_testing = 0


class TeamStat:
    name = ''
    committed = 0
    finished = 0
    fixed_bug = 0
    dev_bug = 0
    logged_time_total = 0
    logged_time_new_feature = 0
    logged_time_dev_bug = 0
    logged_time_existing_bug = 0
    logged_time_testing = 0
    member_stat_summary = {}

    def __init__(self):
        self.member_stat_summary = {}


class MemberStat:
    name = ''
    committed = 0
    finished = 0
    fixed_bug = 0
    dev_bug = 0
    resolved_issue_count = 0
    max_issue_point = 0
    logged_time_total = 0
    logged_time_new_feature = 0
    logged_time_dev_bug = 0
    logged_time_existing_bug = 0
    logged_time_testing = 0
