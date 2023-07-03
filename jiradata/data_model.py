from dateutil import parser

IGNORE_ISSUE_TYPES = ['Epic']
NEW_FEATURE_ISSUE_TYPES = ['Story', 'Change Request', 'Feature Request']
PRIMARY_ISSUE_TYPES = [
    'Story', 'Feature Request', 'Change Request', 'Bug', 'Test Plan', 'Task'
]
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
    labels = []
    reporter = ''
    dev_bug_count = 0

    def __init__(self, obj):
        self.sub_issues = []
        self.contributors = {}
        self.id = obj['id']
        self.key = obj['key']
        self.type = obj['fields']['issuetype']['name']
        self.status = obj['fields']['status']['name']
        self.work_logs = obj['fields']['worklog']['worklogs']
        self.reporter = obj['fields']['reporter']['displayName']
        self.labels = obj['fields']['labels']

        if self.type in IGNORE_ISSUE_TYPES:
            pass
        elif self.type in PRIMARY_ISSUE_TYPES:
            self.resolution_date = obj['fields']['resolutiondate']
            self.story_point = (0 if 'customfield_10026' not in obj['fields']
                                or obj['fields']['customfield_10026'] is None
                                else obj['fields']['customfield_10026'])
        else:
            self.parent_id = obj['fields']['parent']['id']


class SprintSummary():
    id = 0
    name = ''
    state = ''
    start_date = ''
    end_date = ''
    complete_date = ''
    goal = ''
    original_not_completed_point = 0
    original_completed_point = 0
    original_removed_point = 0
    new_not_completed_point = 0
    new_completed_point = 0
    new_removed_point = 0
    outside_completed_point = 0
    outside_not_completed_point = 0
    fixed_bug_count = 0
    dev_bug_count = 0
    new_feature_story_point = 0
    logged_time_total = 0
    logged_time_new_feature = 0
    logged_time_dev_bug = 0
    logged_time_existing_bug = 0
    logged_time_testing = 0

    primary_issues = {}
    team_stat = {}

    def __init__(self, obj):
        contents = obj['contents']
        sprint = obj['sprint']

        newly_added_issue_dict = contents['issueKeysAddedDuringSprint']

        # Handle completed issues within sprint
        for completed_issue in contents['completedIssues']:
            if 'currentEstimateStatistic' not in completed_issue or 'value' not in completed_issue[
                    'currentEstimateStatistic']['statFieldValue']:
                continue

            completed_key = completed_issue['key']
            completed_point = completed_issue['currentEstimateStatistic'][
                'statFieldValue']['value']

            if completed_key in newly_added_issue_dict and newly_added_issue_dict[
                    completed_key] == True:
                self.new_completed_point += completed_point
            else:
                self.original_completed_point += completed_point

        # Handle not completed issues within sprint
        for not_completed_issue in contents[
                'issuesNotCompletedInCurrentSprint']:
            if 'currentEstimateStatistic' not in not_completed_issue or 'value' not in not_completed_issue[
                    'currentEstimateStatistic']['statFieldValue']:
                continue

            not_completed_key = not_completed_issue['key']
            not_completed_point = not_completed_issue[
                'currentEstimateStatistic']['statFieldValue']['value']

            if not_completed_key in newly_added_issue_dict and newly_added_issue_dict[
                    not_completed_key] == True:
                self.new_not_completed_point += not_completed_point
            else:
                self.original_not_completed_point += not_completed_point

        # Handle punted issues
        for punted_issue in contents['puntedIssues']:
            if 'currentEstimateStatistic' not in punted_issue or not 'value' in punted_issue[
                    'currentEstimateStatistic']['statFieldValue']:
                continue

            punted_key = punted_issue['key']
            punted_point = punted_issue['currentEstimateStatistic'][
                'statFieldValue']['value']

            if punted_key in newly_added_issue_dict and newly_added_issue_dict[
                    punted_key] == True:
                self.new_removed_point += punted_point
            else:
                self.original_removed_point += punted_point

        # Handle completed outside of sprint

        self.id = sprint['id']
        self.name = sprint['name']
        self.state = sprint['state']
        self.start_date = parser.parse(sprint['isoStartDate'])
        self.end_date = parser.parse(sprint['isoEndDate'])
        self.complete_date = parser.parse(
            sprint['isoCompleteDate']
        ) if sprint['isoCompleteDate'] != 'None' else 'None'
        self.goal = sprint['goal']
        self.fixed_bug_count = 0
        self.dev_bug_count = 0
        self.new_feature_story_point = 0
        self.logged_time_total = 0
        self.logged_time_new_feature = 0
        self.logged_time_dev_bug = 0
        self.logged_time_existing_bug = 0
        self.logged_time_testing = 0
        self.primary_issues = {}
        self.team_stat = {}


class TeamStat:
    name = ''
    committed = 0
    completed = 0
    fixed_bug = 0
    dev_bug = 0
    committed_issue_count = 0
    resolved_issue_count = 0
    logged_time_total = 0
    logged_time_new_feature = 0
    logged_time_dev_bug = 0
    logged_time_existing_bug = 0
    logged_time_testing = 0
    member_stat_summary = {}
    dev_bug_sum = {}

    def __init__(self):
        self.member_stat_summary = {}


class MemberStat:
    name = ''
    committed = 0
    completed = 0
    fixed_bug = 0
    dev_bug = 0
    report_dev_bug = 0
    committed_issue_count = 0
    resolved_issue_count = 0
    max_committed_issue_point = 0
    max_resolved_issue_point = 0
    logged_time_total = 0
    logged_time_new_feature = 0
    logged_time_dev_bug = 0
    logged_time_existing_bug = 0
    logged_time_testing = 0


class WorkLogInfo:
    author = ''
    duration = 0
    issue_key = ''
    created = None

    def __init__(self, obj, primary_issue_key) -> None:
        self.author = obj['author']['displayName']
        self.duration = obj['timeSpentSeconds']
        self.issue_key = primary_issue_key
        self.created = parser.parse(obj['created'])
