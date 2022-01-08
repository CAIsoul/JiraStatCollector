from logging import critical
from jira import JIRA
from requests.api import request
from requests.auth import HTTPBasicAuth
import json
import requests
import configparser
import os

config = configparser.ConfigParser()
configFilePath = os.path.join(os.path.dirname(__file__) + r'/../app.ini')
config.read(configFilePath, encoding='utf-8')

TF_JIRA_DOMAIN = config.get('JiraInfo', 'TF_JIRA_DOMAIN')
TF_JIRA_EMAIL = config.get('JiraInfo', 'TF_JIRA_EMAIL')
TF_JIRA_TOKEN = config.get('JiraInfo', 'TF_JIRA_TOKEN')

auth = HTTPBasicAuth(TF_JIRA_EMAIL, TF_JIRA_TOKEN)
headers = {"Accept": "application/json"}

jira = JIRA(server=TF_JIRA_DOMAIN, basic_auth=(TF_JIRA_EMAIL, TF_JIRA_TOKEN))


def generateQueryStr(
    sprint_id=0,
    project_key='',
    issue_type='',
):
    # criteriaList = ['issuetype not in ("Test Plan")']
    criteriaList = []

    if sprint_id > 0:
        criteriaList.append('sprint=%i' % sprint_id)

    if len(project_key) > 0:
        criteriaList.append('project=%k' % project_key)

    if len(issue_type) > 0:
        criteriaList.append('issuetype=%t' % issue_type)

    # to ensure that the order will be:
    # Bug -> Sprint Bug -> Sprint Task -> Story
    # sortByStr = ' order by issuetype '

    sortByStr = ' order by key '

    return ' and '.join(criteriaList) + sortByStr


def getIssue(issueKey):
    url = TF_JIRA_DOMAIN + ('/rest/api/2/issue/{}'.format(issueKey))

    response = requests.request("GET", url, headers=headers, auth=auth)

    data = json.loads(response.text)
    return data


def searchIssuesViaRequest(queryStr, includeFields, startAt=0):
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
    issues = data['issues']
    length = len(issues)

    if data['total'] > data['startAt'] + length:
        return issues + searchIssues(queryStr, includeFields, startAt + length)

    return issues


def searchIssues(queryStr, includeFields, startAt=0):
    result = jira.search_issues(queryStr,
                                fields=includeFields,
                                startAt=startAt,
                                maxResults=100)

    if result.total > result.startAt + len(result):
        nextStartAt = startAt + result.maxResults
        return result + searchIssues(queryStr, includeFields, nextStartAt)

    return result


def getSprintIssues(sprint_id):
    queryStr = generateQueryStr(sprint_id=sprint_id)
    includeFields = [
        'key', 'id', 'parent', 'issuetype', 'worklog', 'customfield_10026',
        'resolutiondate', 'status'
    ]

    issues = searchIssues(queryStr, includeFields, 0)

    return issues


def getBoardIssues(board_id, startAt=0):
    url = TF_JIRA_DOMAIN + '/rest/agile/1.0/board/' + str(board_id) + '/issue'
    includeFields = [
        'key', 'id', 'parent', 'issuetype', 'worklog', 'customfield_10026',
        'resolutiondate', 'status'
    ]

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
        return data['issues'] + getBoardIssues(board_id, max)

    return data['issues']


def getSprintInfo(sprint_id):
    url = TF_JIRA_DOMAIN + '/rest/agile/1.0/sprint/' + str(sprint_id)
    headers = {"Accept": "application/json"}
    response = requests.request("GET", url, headers=headers, auth=auth)

    return json.loads(response.text)


def getBoardInfo(board_id):
    url = TF_JIRA_DOMAIN + '/rest/agile/1.0/board/' + str(board_id)
    headers = {"Accept": "application/json"}
    response = requests.request("GET", url, headers=headers, auth=auth)

    return json.loads(response.text)
