from logging import critical
from jira import JIRA
from requests.api import request
from requests.auth import HTTPBasicAuth
import json
import requests
import configparser
import os

from jiradata.data_model import JiraIssue

config = configparser.ConfigParser()
configFilePath = os.path.join(os.path.dirname(__file__) + r'/../app.ini')
config.read(configFilePath, encoding='utf-8')

TF_JIRA_DOMAIN = config.get('Jira', 'DOMAIN')
TF_JIRA_EMAIL = config.get('Jira', 'EMAIL')
TF_JIRA_TOKEN = config.get('Jira', 'TOKEN')

auth = HTTPBasicAuth(TF_JIRA_EMAIL, TF_JIRA_TOKEN)
headers = {"Accept": "application/json"}

jira = JIRA(server=TF_JIRA_DOMAIN, basic_auth=(TF_JIRA_EMAIL, TF_JIRA_TOKEN))

BASIC_FIELDS = [
    'key', 'id', 'parent', 'issuetype', 'worklog', 'customfield_10026',
    'resolutiondate', 'status'
]


def generateQueryStr(
    sprint_id=0,
    project_key='',
    issue_type='',
    issue_keys=[],
):
    criteriaList = []

    if sprint_id > 0:
        criteriaList.append('sprint=%i' % sprint_id)

    if len(project_key) > 0:
        criteriaList.append('project=%k' % project_key)

    if len(issue_type) > 0:
        criteriaList.append('issuetype=%t' % issue_type)

    if len(issue_keys) > 0:
        issue_type_str = ','.join(
            list(map(lambda x: '"' + x + '"', issue_keys)))
        criteriaList.append('issuekey in ({}) or parent in ({})'.format(
            issue_type_str, issue_type_str))

    sortByStr = ' order by key '

    return ' and '.join(criteriaList) + sortByStr


# Search for all issues
def searchIssues(queryStr, includeFields, startAt=0):
    url = TF_JIRA_DOMAIN + '/rest/api/2/search'
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json"
    }
    payload = json.dumps({
        "jql": queryStr,
        "maxResults": 100,
        "fields": includeFields,
        "startAt": startAt
    })

    response = requests.request("POST",
                                url,
                                data=payload,
                                headers=headers,
                                auth=auth)

    data = json.loads(response.text)
    issues = data["issues"]
    length = len(issues)

    if data['total'] > data['startAt'] + length:
        return issues + searchIssues(queryStr, includeFields, startAt + length)

    return issues


# get issues by sprint id
def getIssuesBySprintId(sprint_id):
    queryStr = generateQueryStr(sprint_id=sprint_id)
    includeFields = BASIC_FIELDS + ['reporter', 'labels']

    issues = searchIssues(queryStr, includeFields, 0)

    primaryIssues = []

    return issues


# get issues by keys
def getIssuesByKeys(issue_keys):
    queryStr = generateQueryStr(issue_keys=issue_keys)
    includeFields = BASIC_FIELDS + ['reporter', 'labels']

    issues = searchIssues(queryStr, includeFields, 0)

    return issues


# get issues by board id
def getIssuesByBoardId(board_id, startAt=0):
    url = TF_JIRA_DOMAIN + '/rest/agile/1.0/board/' + str(board_id) + '/issue'
    includeFields = BASIC_FIELDS

    response = requests.get(url,
                            params={
                                'maxResults': 200,
                                'fields': includeFields
                            },
                            headers=headers,
                            auth=auth)

    data = json.loads(response.text)

    max = data['startAt'] + data['maxResults']

    if max < data['total']:
        return data['issues'] + getIssuesByBoardId(board_id, max)

    return data['issues']


def getSprintInfo(sprint_id):
    url = TF_JIRA_DOMAIN + '/rest/agile/1.0/sprint/' + str(sprint_id)
    response = requests.request("GET", url, headers=headers, auth=auth)

    return json.loads(response.text)


def getBoardInfo(board_id):
    url = TF_JIRA_DOMAIN + '/rest/agile/1.0/board/' + str(board_id)
    response = requests.request("GET", url, headers=headers, auth=auth)

    return json.loads(response.text)


def getSprintReportInfo(sprint_id):
    sprint_report_view_id = 53
    url = TF_JIRA_DOMAIN + '/rest/greenhopper/latest/rapid/charts/sprintreport?rapidViewId={}&sprintId={}'.format(
        sprint_report_view_id, sprint_id)

    response = requests.request("GET", url, headers=headers, auth=auth)

    return json.loads(response.text)


def getSprintIssueDict(sprint_id):
    all_issues = list(
        map(lambda x: JiraIssue(x), getIssuesBySprintId(sprint_id)))

    primary_issue_dict = {}

    for issue in all_issues:
        if issue.is_primary() == True:
            primary_issue_dict[issue.id] = issue

    for issue in all_issues:
        if issue.is_primary() == True:
            continue

        parent_issue = primary_issue_dict[issue.parent_id]

        if parent_issue is not None:
            parent_issue.sub_issues.append(issue)

    return primary_issue_dict
