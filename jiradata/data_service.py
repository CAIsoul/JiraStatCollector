from jira import JIRA
from requests.api import request
from requests.auth import HTTPBasicAuth
import json
import requests
import configparser
import os

from jiradata.data_model import IGNORE_ISSUE_TYPES, PRIMARY_ISSUE_TYPES, JiraIssue

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
    sprint_id = int(sprint_id)

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
    issues = list(map(lambda x: JiraIssue(x), issues))

    return issues


# get issues by keys
def getIssuesByKeys(issue_keys):
    queryStr = generateQueryStr(issue_keys=issue_keys)
    includeFields = BASIC_FIELDS + ['reporter', 'labels']

    issues = searchIssues(queryStr, includeFields, 0)
    issues = list(map(lambda x: JiraIssue(x), issues))

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


def getSprintReportInfo(board_id, sprint_id):
    url = TF_JIRA_DOMAIN + '/rest/greenhopper/latest/rapid/charts/sprintreport?rapidViewId={}&sprintId={}'.format(
        board_id, sprint_id)

    response = requests.request("GET", url, headers=headers, auth=auth)

    return json.loads(response.text)


def getMemberWorklogs(member_list, start_date, end_date, start_at=0):
    author_param = "('" + "','".join(member_list) + "')"
    url = TF_JIRA_DOMAIN + '/rest/api/2/search'

    start_date_str = start_date.strftime("%Y-%m-%d")
    end_date_str = end_date.strftime("%Y-%m-%d")

    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json"
    }
    payload = json.dumps({
        "jql":
        "worklogAuthor in {} and worklogDate >= '{}' and worklogDate <= '{}'".
        format(author_param, start_date_str, end_date_str),
        "maxResults":
        100,
        "fields": ['worklog'],
        "startAt":
        start_at
    })

    response = requests.request("POST",
                                url,
                                data=payload,
                                headers=headers,
                                auth=auth)

    data = json.loads(response.text)
    issues = data["issues"]
    total = int(data["total"])

    if len(issues) + start_at < total:
        issues += getMemberWorklogs(member_list, start_date, end_date,
                                    len(issues))

    return issues


def getSprintIssueDict(sprint_id):
    all_issues = getIssuesBySprintId(sprint_id)

    primary_issue_dict = {}

    # Process primary issues in the first iteration
    for issue in all_issues:
        if issue.type in PRIMARY_ISSUE_TYPES:
            primary_issue_dict[issue.id] = issue

    # Process other issues in the second iteration.
    for issue in all_issues:
        if issue.type in IGNORE_ISSUE_TYPES or issue.type in PRIMARY_ISSUE_TYPES:
            continue

        parent_issue = primary_issue_dict[issue.parent_id]

        if parent_issue is not None:
            parent_issue.sub_issues.append(issue)

    return primary_issue_dict


def getWorklogsByAuthorAndDateRange(author, start_date, end_date):
    url = TF_JIRA_DOMAIN + '/rest/api/2/search'
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json"
    }
    payload = json.dumps({
        "jql":
        "worklogAuthor='{}' and worklogDate >= '{}' and worklogDate <= '{}'".
        format(author, start_date, end_date),
        "maxResults":
        100,
    })

    response = requests.request("POST",
                                url,
                                data=payload,
                                headers=headers,
                                auth=auth)

    data = json.loads(response.text)

    return data


def getBoards(start_at=0):
    url = TF_JIRA_DOMAIN + '/rest/agile/1.0/board'
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json"
    }

    boards = []
    response = requests.request("GET", 
                                url,
                                params={
                                    'startAt': start_at,
                                },
                                headers=headers, 
                                auth=auth)

    data = json.loads(response.text)

    boards = boards + data["values"]

    if data["maxResults"] + data["startAt"] < data["total"]:
        boards = boards + getBoards(start_at=data["startAt"] + data["maxResults"])

    return boards


def getSprintsForBoard(board_id, start_at=0):
    url = TF_JIRA_DOMAIN + f"/rest/agile/1.0/board/{board_id}/sprint"
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json"
    }

    sprints = []
    response = requests.request("GET",
                                url,
                                params={
                                    'startAt': start_at,
                                },
                                headers=headers,
                                auth=auth)

    data = json.loads(response.text)

    sprints = sprints + data["values"]

    if start_at + data["maxResults"] < data["total"]:
        sprints = sprints + getSprintsForBoard(
            board_id, start_at=start_at + data["maxResults"])

    return sprints


def getIssuesForSprint(sprint_id, start_at=0):
    url = TF_JIRA_DOMAIN + f"/rest/agile/1.0/sprint/{sprint_id}/issue"

    issues = []
    response = requests.request("GET",
                                url,
                                params={
                                    'startAt': start_at,
                                    'fields': 'summary,issuetype,status,priority,timespent,aggregatetimespent,aggregatetimeoriginalestimate,timeoriginalestimate,description,updated,duedate,resolutiondate,reporter,project,sprint,worklog,parent,closedSprints,subtasks,customfield_10026,customfield_10042'
                                },
                                headers=headers,
                                auth=auth)

    data = json.loads(response.text)

    issues = issues + data["issues"]

    if start_at + data["maxResults"] < data["total"]:
        issues = issues + getIssuesForSprint(
            sprint_id, start_at=start_at + data["maxResults"])

    return issues