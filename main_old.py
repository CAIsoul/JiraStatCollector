import csv
from datetime import timedelta
import re

from dateutil import parser
import jiradata.data_service as data
import jiradata.data_process as process

BASE_OUTPUT_FOLDER = 'output'
NEW_FEATURE_ISSUE_TYPES = ['Story', 'Change Request']
PRIMARY_ISSUE_TYPES = ['Story', 'Change Request', 'Bug']
SUB_ISSUE_TYPES = ['Sprint Bug', 'Sprint Task', 'Sub Test Execution']
TEST_ISSUE_TYPES = ['Test Execution', 'Test Case']
DONE_ISSUE_STATUSES = ['Done', 'Resolved', 'Fixed', 'Closed']


class sprintSummary():
    name = ''
    assigned = 0
    finished = 0
    fixed = 0
    devBug = 0
    newFeature = 0
    totalLoggedTime = 0
    loggedTimeOnNewFeature = 0
    loggedTimeOnDevelopmentBug = 0
    loggedTimeOnExistingBug = 0
    loggedTimeOnTestingDevBug = 0


class issueSummary():
    storyPoint = 0
    issueType = ''
    status = ''
    contributors = {}
    mainContributor = ''
    resolutionDate = ''


class developerEffort():
    timeLogged = 0
    assignedStoryCount = 0
    assignedStoryPoint = 0
    finishedStoryCount = 0
    finishedStoryPoint = 0
    largestSingleAssignedStoryPoint = 0
    largestSingleFinishedStoryPoint = 0
    fixedBugCount = 0

    def append(self,
               timeLogged=0,
               assignedStoryPoint=0,
               finishedStoryPoint=0,
               fixedBugCount=0):
        self.timeLogged += timeLogged
        self.assignedStoryPoint += assignedStoryPoint
        self.finishedStoryPoint += finishedStoryPoint
        self.fixedBugCount += fixedBugCount


def gatherSprintInformation(issues, endDate):
    summary = sprintSummary()

    for issue in issues:

        issueType = issue.fields.issuetype.name
        issueStatus = issue.fields.status.name

        if hasattr(issue.fields, 'customfield_10026'
                   ) and issue.fields.customfield_10026 is not None:
            summary.assigned += issue.fields.customfield_10026

            if (issueStatus in DONE_ISSUE_STATUSES
                    and issue.fields.resolutiondate is not None
                    and issue.fields.resolutiondate < endDate):
                summary.finished += issue.fields.customfield_10026

                if issueType in NEW_FEATURE_ISSUE_TYPES:
                    summary.newFeature += issue.fields.customfield_10026

        if issueStatus in DONE_ISSUE_STATUSES:
            if issueType == 'Bug':
                summary.fixed += 1
            elif issueType == 'Sprint Bug':
                summary.devBug += 1

        for log in issue.fields.worklog.worklogs:
            summary.totalLoggedTime += log.timeSpentSeconds

            if issueType == 'Bug':
                summary.loggedTimeOnExistingBug += log.timeSpentSeconds
            elif issueType == 'Sprint Bug':
                summary.loggedTimeOnDevelopmentBug += log.timeSpentSeconds
            elif issueType == 'Sprint Task' or issueType in NEW_FEATURE_ISSUE_TYPES:
                summary.loggedTimeOnNewFeature += log.timeSpentSeconds
            elif issueType == 'Sub Test Execution':
                summary.loggedTimeOnTestingDevBug += log.timeSpentSeconds

    return summary


def gatherDevInformation2(issues, startdate, endDate):
    developerSummary = {}
    primaryIssueSummary = {}
    acceptableEndDate = parser.parse(endDate) + timedelta(days=1)

    for issue in issues:
        issueType = issue.fields.issuetype.name
        primaryIssueKey = ''
        primaryIssueStoryPoint = 0
        primaryIssueStatus = ''
        primaryIssueType = ''

        if issueType in PRIMARY_ISSUE_TYPES:
            primaryIssueKey = issue.key
            primaryIssueStoryPoint = issue.fields.customfield_10026
            primaryIssueStatus = issue.fields.status.name
            primaryIssueType = issueType
        elif issueType in SUB_ISSUE_TYPES:
            primaryIssueKey = issue.fields.parent.key
        else:
            primaryIssueKey = issue.key

        if primaryIssueKey not in primaryIssueSummary:
            primaryIssueSummary[primaryIssueKey] = issueSummary()
            primaryIssueSummary[primaryIssueKey].contributors = {}
            primaryIssueSummary[
                primaryIssueKey].resolutionDate = issue.fields.resolutiondate

        if primaryIssueStoryPoint is not None and primaryIssueStoryPoint > 0:
            primaryIssueSummary[
                primaryIssueKey].storyPoint = primaryIssueStoryPoint

        if primaryIssueStatus is not None and primaryIssueStatus != '':
            primaryIssueSummary[primaryIssueKey].status = primaryIssueStatus

        if primaryIssueType is not None and primaryIssueType != '':
            primaryIssueSummary[primaryIssueKey].issueType = primaryIssueType

        for log in issue.fields.worklog.worklogs:
            authorName = log.author.displayName
            if authorName not in developerSummary:
                developerSummary[authorName] = developerEffort()

            developerSummary[authorName].append(
                timeLogged=log.timeSpentSeconds)

            if authorName not in primaryIssueSummary[
                    primaryIssueKey].contributors:
                primaryIssueSummary[primaryIssueKey].contributors[
                    authorName] = log.timeSpentSeconds
            else:
                primaryIssueSummary[primaryIssueKey].contributors[
                    authorName] += log.timeSpentSeconds

    for key in primaryIssueSummary:
        maxTime = 0
        mainContributor = ''

        for name in primaryIssueSummary[key].contributors:
            if primaryIssueSummary[key].contributors[name] > maxTime:
                mainContributor = name
                maxTime = primaryIssueSummary[key].contributors[name]

        if mainContributor in developerSummary:
            developerSummary[mainContributor].assignedStoryCount += 1
            developerSummary[
                mainContributor].assignedStoryPoint += primaryIssueSummary[
                    key].storyPoint
            if primaryIssueSummary[key].storyPoint > developerSummary[
                    mainContributor].largestSingleAssignedStoryPoint:
                developerSummary[
                    mainContributor].largestSingleAssignedStoryPoint = primaryIssueSummary[
                        key].storyPoint

            if (primaryIssueSummary[key].status in DONE_ISSUE_STATUSES
                    and parser.parse(primaryIssueSummary[key].resolutionDate) <
                    acceptableEndDate):
                developerSummary[mainContributor].finishedStoryCount += 1
                developerSummary[
                    mainContributor].finishedStoryPoint += primaryIssueSummary[
                        key].storyPoint
                if primaryIssueSummary[key].storyPoint > developerSummary[
                        mainContributor].largestSingleFinishedStoryPoint:
                    developerSummary[
                        mainContributor].largestSingleFinishedStoryPoint = primaryIssueSummary[
                            key].storyPoint

                if primaryIssueSummary[key].issueType == 'Bug':
                    developerSummary[mainContributor].fixedBugCount += 1

    return {'dev': developerSummary, 'issue': primaryIssueSummary}


def exportSprintOverviewToCsv(sprintIds):
    sprintSummaryList = []

    for id in sprintIds:
        info = data.getSprintInfo(id)
        issues = data.getSprintIssues(id)
        summary = gatherSprintInformation(issues, info['endDate'])
        summary.name = info['name']

        sprintSummaryList.append(summary)

    with open('output/sprint-review.csv', mode='w', newline='') as review_file:
        review_writter = csv.writer(review_file,
                                    delimiter=',',
                                    quotechar='"',
                                    quoting=csv.QUOTE_MINIMAL)

        review_writter.writerow([
            'Sprint Name', 'Assigned', 'Finished', 'Not Finished',
            'Fixed Existing Bugs', 'Development Bugs', 'Completeness',
            'New Feature Ratio'
        ])

        for summary in sprintSummaryList:
            review_writter.writerow([
                summary.name,
                str(summary.assigned),
                str(summary.finished),
                str(summary.assigned - summary.finished),
                str(summary.fixed),
                str(summary.devBug),
                str(100 * summary.finished / summary.assigned) + "%",
                str(100 * summary.newFeature / summary.finished) + "%",
            ])

    print('Successfully export sprint-review.csv file!')


def drawSprintReviewGraph(sprintIds):
    sprintSummaryList = []

    for id in sprintIds:
        info = data.getSprintInfo(id)
        issues = data.getSprintIssues(id)
        summary = gatherSprintInformation(issues)
        summary.name = info['name']

        sprintSummaryList.append(summary)

    # plt.plot(x)


def calculateDevContribution(issues, startDate):
    primaryIssueSummary = {}

    for issue in issues:
        if (issue.fields.resolutiondate is not None
                and issue.fields.resolutiondate < startDate):
            continue

        issueType = issue.fields.issuetype.name
        primaryIssueKey = ''

        if issueType in NEW_FEATURE_ISSUE_TYPES:
            primaryIssueKey = issue.key
        elif issueType in SUB_ISSUE_TYPES:
            primaryIssueKey = issue.fields.parent.key
        else:
            continue

        if primaryIssueKey not in primaryIssueSummary:
            primaryIssueSummary[primaryIssueKey] = issueSummary()
            primaryIssueSummary[primaryIssueKey].contributors = {}

        primaryIssueData = primaryIssueSummary[primaryIssueKey]

        if issueType in NEW_FEATURE_ISSUE_TYPES:
            primaryIssueData.storyPoint = issue.fields.customfield_10026
            primaryIssueData.status = issue.fields.status.name

        for log in issue.fields.worklog.worklogs:
            authorName = log.author.displayName
            if authorName not in primaryIssueData.contributors:
                primaryIssueData.contributors[authorName] = 0

            primaryIssueData.contributors[authorName] += log.timeSpentSeconds

    return primaryIssueSummary


def exportIssueContributors(issues, startDate):
    summary = calculateDevContribution(issues, startDate)
    developers = []

    for key in summary:
        max = 0
        mainContributor = ''
        for dev in summary[key].contributors:
            if dev not in developers:
                developers.append(dev)

            if summary[key].contributors[dev] > max:
                max = summary[key].contributors[dev]
                mainContributor = dev

        summary[key].mainContributor = mainContributor

    developers.sort()

    outputFilename = BASE_OUTPUT_FOLDER + '/sprint-issue-contributors.csv'
    with open(outputFilename, mode='w', newline='') as review_file:
        summary_writter = csv.writer(review_file,
                                     delimiter=',',
                                     quotechar='"',
                                     quoting=csv.QUOTE_MINIMAL)

        summary_writter.writerow(['Issue Key\\Developer'] + developers +
                                 ['Status', 'Total'])

        for key in summary:
            issueData = summary[key]
            contribution = list(
                map(
                    lambda name: 0 if issueData.mainContributor != name else
                    issueData.storyPoint, developers))
            summary_writter.writerow([key] + contribution +
                                     [issueData.status, issueData.storyPoint])

    print('Sprint Issue Contribution Exported.')


def exportSprintOverview(sprintId):
    sprintInfo = data.getSprintInfo(sprintId)
    sprintIssues = data.getSprintIssues(sprintId)
    sprintReview = gatherSprintInformation(sprintIssues, sprintInfo['endDate'])
    # sortedIssues = sortSprintData(sprintIssues)
    # primary_issue_summary = process.process_issue_list(sprintIssues)

    # sprint_start = parser.parse(sprintInfo['startDate'])
    # sprint_end = parser.parse(sprintInfo['endDate'])
    # sprint_summary = process.summarize_sprint_stat(
    #     primary_issue_summary, sprint_start, sprint_end)

    result = gatherDevInformation2(sprintIssues, sprintInfo['startDate'],
                                   sprintInfo['endDate'])

    outputFilename = BASE_OUTPUT_FOLDER + \
        '/sprint-overview (' + (re.sub('/', '-', sprintInfo['name'])) + ').csv'

    with open(outputFilename, mode='w', newline='') as review_file:
        summary_writter = csv.writer(review_file,
                                     delimiter=',',
                                     quotechar='"',
                                     quoting=csv.QUOTE_MINIMAL)

        summary_writter.writerow([sprintInfo['name']])
        summary_writter.writerow([])

        summary_writter.writerow(['Sprint Overview:'])
        summary_writter.writerow([
            'Completed/Committed:',
            str(sprintReview.finished) + '/' + str(sprintReview.assigned)
        ])
        summary_writter.writerow([
            'Total Hours Logged:',
            round(sprintReview.totalLoggedTime / 60 / 60, 1)
        ])
        summary_writter.writerow([
            'New Feature Development:',
            str(100 * (sprintReview.loggedTimeOnNewFeature /
                       sprintReview.totalLoggedTime)) +
            "%" if sprintReview.totalLoggedTime > 0 else 0
        ])
        summary_writter.writerow([
            'Development Bugs:',
            str(100 * (sprintReview.loggedTimeOnDevelopmentBug /
                       sprintReview.totalLoggedTime)) +
            "%" if sprintReview.totalLoggedTime > 0 else 0
        ])
        summary_writter.writerow([
            'Existing Bugs:',
            str(100 * (sprintReview.loggedTimeOnExistingBug /
                       sprintReview.totalLoggedTime)) +
            "%" if sprintReview.totalLoggedTime > 0 else 0
        ])
        summary_writter.writerow([
            'New Feature Testing:',
            str(100 * (sprintReview.loggedTimeOnTestingDevBug /
                       sprintReview.totalLoggedTime)) +
            "%" if sprintReview.totalLoggedTime > 0 else 0
        ])

        summary_writter.writerow([])
        summary_writter.writerow([])

        summary_writter.writerow(['Member Overview:'])
        summary_writter.writerow([
            'Member', 'Total Hours Logged', 'Assigned Count', 'Assigned Point',
            'Avg. Assigned Point', 'Max Single Assigned Point',
            'Assigned Contribution', 'Finished Count', 'Finished Point',
            'Avg. Finished Point', 'Max Single Finished Point',
            'Finished Contribution', 'Fix Existing Bug Count', 'Completeness'
        ])

        devSummary = result['dev']
        issueSummary = result['issue']

        for dev in list(devSummary):
            devInfo = devSummary[dev]
            summary_writter.writerow([
                dev,
                round(devInfo.timeLogged / 60 / 60, 1),
                devInfo.assignedStoryCount,
                round(devInfo.assignedStoryPoint, 1),
                0 if devInfo.assignedStoryCount <= 0 else round(
                    devInfo.assignedStoryPoint /
                    devInfo.assignedStoryCount, 2),
                devInfo.largestSingleAssignedStoryPoint,
                str(100 *
                    (devInfo.assignedStoryPoint / sprintReview.assigned)) +
                "%" if sprintReview.assigned > 0 else 0,
                devInfo.finishedStoryCount,
                round(devInfo.finishedStoryPoint, 1),
                0 if devInfo.finishedStoryCount <= 0 else round(
                    devInfo.finishedStoryPoint /
                    devInfo.finishedStoryCount, 2),
                devInfo.largestSingleFinishedStoryPoint,
                str(100 *
                    (devInfo.finishedStoryPoint / sprintReview.finished)) +
                "%" if sprintReview.finished > 0 else 0,
                devInfo.fixedBugCount,
                str(100 *
                    (devInfo.finishedStoryPoint / devInfo.assignedStoryPoint))
                + "%" if devInfo.assignedStoryPoint > 0 else 0,
            ])

        summary_writter.writerow(['Primary Issue Overview:'])
        summary_writter.writerow([
            'Issue Key',
            'Issue Type',
            'Story Point',
            'Resolved',
        ] + list(devSummary.keys()))

        for key in issueSummary:
            issue_data = issueSummary[key]

            member_contribution = []

            for dev in list(devSummary):
                if dev in issue_data.contributors:
                    member_contribution.append(
                        round(issue_data.contributors[dev] / 60 / 60, 2))
                else:
                    member_contribution.append(0)

            summary_writter.writerow([
                key,
                issue_data.issueType,
                issue_data.storyPoint,
                issue_data.status in DONE_ISSUE_STATUSES,
            ] + member_contribution)

        summary_writter.writerow([])
        summary_writter.writerow([])
        summary_writter.writerow([
            'Sprint Used:', sprintId, sprintInfo['startDate'],
            sprintInfo['endDate']
        ])

    print('Sprint Overview Exported.')


# exportSprintOverview(1441)
# exportSprintOverview(1456)
# exportSprintOverview(1459)
# exportSprintOverview(1465)
# exportSprintOverview(1472)
# exportSprintOverview(1485)
exportSprintOverview(1493)

# Team 1 -
# Team 2 - 1473
# Team 3 - 1472
# Team 4 - 1455
# Team 5 - Kanban
# Team 6 - 1482
# Team 7 - 1483

pass
