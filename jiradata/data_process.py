import pytz
import datetime
import time
from dateutil import parser
from jiradata.data_model import JiraIssue, TeamStat, MemberStat, WorkLogInfo

NEW_FEATURE_ISSUE_TYPES = ['Story', 'Change Request']
PRIMARY_ISSUE_TYPES = ['Story', 'Change Request', 'Bug']
SUB_ISSUE_TYPES = ['Sprint Bug', 'Sprint Task', 'Sub Test Execution']
TEST_ISSUE_TYPES = ['Test Execution', 'Test Case']
DONE_ISSUE_STATUSES = ['Done', 'Resolved', 'Fixed', 'Closed']


# pre-process issues, pick up primary issues and put sub issues within their 'parent' issue
def process_issue_list(issue_list):
    primary_issue_summary = {}

    for issue in issue_list:
        issue_data = JiraIssue()
        issue_data.load(issue)
        primary_issue_data = None

        if issue_data.is_primary():
            if issue_data.id not in primary_issue_summary:
                primary_issue_summary[issue_data.id] = issue_data
            else:
                primary_issue_summary[issue_data.id].load(issue_data)

            primary_issue_data = primary_issue_summary[issue_data.id]

        elif issue_data.parent_id is not None:
            if issue_data.parent_id not in primary_issue_summary:
                parent_issue = JiraIssue()
                parent_issue.init_parent_issue(issue_data)
                primary_issue_summary[parent_issue.id] = parent_issue

            primary_issue_data = primary_issue_summary[issue_data.parent_id]
            primary_issue_data.sub_issues.append(issue_data)

    return primary_issue_summary


# summarize sprint stat
def summarize_sprint_stat(primary_issue_summary, sprint_start, sprint_end,
                          developer_list, tester_list, share_pattern):
    team_stat = TeamStat()
    member_stat_dict = {}

    for id in list(primary_issue_summary):
        issue_data = primary_issue_summary[id]

        calculateMainContributor(issue_data, sprint_start, sprint_end)

        accumulatePrimaryIssueStatForSprint(issue_data, team_stat,
                                            member_stat_dict, sprint_start,
                                            sprint_end, developer_list,
                                            tester_list, share_pattern)

    team_stat.member_stat_summary = member_stat_dict

    team_stat.logged_time_total = (team_stat.logged_time_new_feature +
                                   team_stat.logged_time_dev_bug +
                                   team_stat.logged_time_existing_bug +
                                   team_stat.logged_time_testing)

    return team_stat


#summarize kanban stat
def summarize_kanban_stat(primary_issue_summary, review_start, review_end):
    team_stat = TeamStat()
    member_stat_dict = {}

    for id in list(primary_issue_summary):
        issue_data = primary_issue_summary[id]

        calculateMainContributor(issue_data)

        accumulatePrimaryIssueStatForKanban(issue_data, team_stat,
                                            member_stat_dict, review_start,
                                            review_end)

    team_stat.member_stat_summary = member_stat_dict

    return team_stat


# Get member stat from cache or initialize a new one
def getMemberStatData(dict, key):
    if key not in dict:
        dict[key] = MemberStat()

    return dict[key]


# check if date str is within given start and end dates, skip if not value specified
def matchDateRangeLimit(dateStr, start_date=None, end_date=None):
    if start_date is not None or end_date is not None:
        date = parser.parse(dateStr)

        return ((start_date is not None and date < start_date)
                or (end_date is not None and date > end_date)) == False

    return True


# accumulate sprint stat from primary issues (including sub-issues)
# share pattern determines how a story point is shared if multiple developers have worked together
def accumulatePrimaryIssueStatForSprint(issue_data,
                                        team_stat,
                                        member_stat_dict,
                                        start_date=None,
                                        end_date=None,
                                        developer_list=[],
                                        tester_list=[],
                                        share_pattern=1):

    # each primary issue is counted as one in committed issues
    team_stat.committed_issue_count += 1

    # check whether an issue is resolved
    is_resolved = False
    if issue_data.resolution_date is not None and issue_data.resolution_date != '':
        is_resolved = matchDateRangeLimit(issue_data.resolution_date,
                                          start_date, end_date)

        if is_resolved:
            team_stat.resolved_issue_count += 1

    #  calcuate story point
    if issue_data.story_point is not None and issue_data.story_point > 0:
        team_stat.committed += issue_data.story_point

        if is_resolved:
            team_stat.finished += issue_data.story_point

        distributeIssueTrophies(member_stat_dict, issue_data, is_resolved,
                                developer_list, tester_list, share_pattern)

    # process work logs
    if issue_data.type in NEW_FEATURE_ISSUE_TYPES:

        handlePrimeryIssue(issue_data, start_date, end_date, team_stat,
                           member_stat_dict)

    elif issue_data.type == 'Bug':

        if is_resolved:
            team_stat.fixed_bug += 1
            getMemberStatData(member_stat_dict,
                              issue_data.main_contributor).fixed_bug += 1

        handlePrimeryIssue(issue_data, start_date, end_date, team_stat,
                           member_stat_dict)

    elif issue_data.type == 'Test Plan':
        handlePrimeryIssue(issue_data, start_date, end_date, team_stat,
                           member_stat_dict)

    else:
        handlePrimeryIssue(issue_data, start_date, end_date, team_stat,
                           member_stat_dict)


# accumulate kanban stat from primary issues (including sub-issues)
def accumulatePrimaryIssueStatForKanban(issue_data,
                                        team_stat,
                                        member_stat_dict,
                                        start_date=None,
                                        end_date=None):
    is_resolved = False

    if issue_data.resolution_date is not None and issue_data.resolution_date != '':
        is_resolved = matchDateRangeLimit(issue_data.resolution_date,
                                          start_date, end_date)

    if is_resolved and issue_data.story_point > 0:
        team_stat.finished += issue_data.story_point

        if issue_data.main_contributor != '':
            main_contributor_stat = getMemberStatData(
                member_stat_dict, issue_data.main_contributor)
            main_contributor_stat.finished += issue_data.story_point
            main_contributor_stat.resolved_issue_count += 1

            if (main_contributor_stat.max_resolved_issue_point <= 0
                    or issue_data.story_point >
                    main_contributor_stat.max_resolved_issue_point):
                main_contributor_stat.max_resolved_issue_point = issue_data.story_point

    if issue_data.type in NEW_FEATURE_ISSUE_TYPES:

        for log in issue_data.work_logs:
            if matchDateRangeLimit(log['created'], start_date,
                                   end_date) == False:
                continue

            logged_time = log['timeSpentSeconds']
            member_name = log['author']['displayName']

            team_stat.logged_time_new_feature += logged_time
            getMemberStatData(
                member_stat_dict,
                member_name).logged_time_new_feature += logged_time

        for sub_issue in issue_data.sub_issues:

            for log in sub_issue.work_logs:
                if matchDateRangeLimit(log['created'], start_date,
                                       end_date) == False:
                    continue

                logged_time = log['timeSpentSeconds']
                member_name = log['author']['displayName']

                if sub_issue.type == 'Sprint Task':
                    team_stat.logged_time_new_feature += logged_time
                    getMemberStatData(
                        member_stat_dict,
                        member_name).logged_time_new_feature += logged_time

                elif sub_issue.type == 'Sprint Bug':
                    team_stat.logged_time_dev_bug += logged_time
                    getMemberStatData(
                        member_stat_dict,
                        member_name).logged_time_dev_bug += logged_time
                    getMemberStatData(member_stat_dict,
                                      issue_data.main_contributor).dev_bug += 1

                elif sub_issue.type == 'Test Case' or sub_issue.type == 'Sub Test Execution':
                    team_stat.logged_time_testing += logged_time
                    getMemberStatData(
                        member_stat_dict,
                        member_name).logged_time_testing += logged_time

                else:
                    team_stat.logged_time_new_feature += logged_time
                    getMemberStatData(
                        member_stat_dict,
                        member_name).logged_time_new_feature += logged_time

    elif issue_data.type == 'Bug':

        if is_resolved:
            team_stat.fixed_bug += 1
            getMemberStatData(member_stat_dict,
                              issue_data.main_contributor).fixed_bug += 1

        for log in issue_data.work_logs:
            if matchDateRangeLimit(log['created'], start_date,
                                   end_date) == False:
                continue

            logged_time = log['timeSpentSeconds']
            member_name = log['author']['displayName']

            team_stat.logged_time_existing_bug += logged_time
            getMemberStatData(
                member_stat_dict,
                member_name).logged_time_existing_bug += logged_time

    elif issue_data.type == 'Test Plan':
        for log in issue_data.work_logs:
            if matchDateRangeLimit(log['created'], start_date,
                                   end_date) == False:
                continue

            if matchDateRangeLimit(log['created'], start_date, end_date):
                logged_time = log['timeSpentSeconds']
                member_name = log['author']['displayName']

                team_stat.logged_time_testing += logged_time
                getMemberStatData(
                    member_stat_dict,
                    member_name).logged_time_testing += logged_time

    else:
        pass


# determine the main contributor for the primary issue
def calculateMainContributor(primary_issue, start_date=None, end_date=None):
    contributor_summary = {}

    appendContributionFromLogs(primary_issue.work_logs, contributor_summary,
                               start_date, end_date)

    for sub_issue in primary_issue.sub_issues:
        appendContributionFromLogs(sub_issue.work_logs, contributor_summary,
                                   start_date, end_date)

    primary_issue.contributors = contributor_summary


# accumulate member work logs
def appendContributionFromLogs(log_list,
                               contributor_summary,
                               start_date=None,
                               end_date=None):
    for log in log_list:
        if start_date is not None or end_date is not None:
            log_created_date = parser.parse(log['created'])

            if ((start_date is not None and log_created_date < start_date)
                    or end_date is not None and log_created_date > end_date):
                continue

        name = log['author']['displayName']

        if name not in contributor_summary:
            contributor_summary[name] = 0

        contributor_summary[name] += log['timeSpentSeconds']


def datetime2Utc(original_datetime):
    local_time = original_datetime.astimezone(pytz.timezone('Asia/Shanghai'))
    # da = datetime.strftime(local_time, '%Y-%m-%d %H:%M:%S')
    last_id = time.mktime(local_time.timetuple())
    return time.localtime(last_id)


def summarizedSprintWorkLogs(issue_list, start_date, end_date):
    work_log_summary = {}

    for issue in issue_list:
        for log in issue['fields']['worklog']['worklogs']:
            log_time = parser.parse(log['created'])

            log_time += datetime.timedelta(hours=13)

            if log_time < start_date or log_time > end_date:
                continue
            else:
                time_delta = log_time - start_date
                if time_delta.days not in work_log_summary:
                    work_log_summary[time_delta.days] = []

                work_log_info = WorkLogInfo(log, issue['key'])

                work_log_summary[time_delta.days].append(work_log_info)

    return work_log_summary


# distribute primary issue trophies to involved members
def distributeIssueTrophies(member_stat_dict, issue_data, is_resolved,
                            developer_list, tester_list, share_pattern):
    share_dict = {}

    # calculate story point share for different patterns
    if share_pattern == 1:
        share_dict = winnerGetsAll(issue_data.contributors,
                                   issue_data.story_point, developer_list,
                                   tester_list)
    else:
        share_dict = shareByLoggedTime(issue_data.contributors,
                                       issue_data.story_point, developer_list,
                                       tester_list)

    for member in list(share_dict):
        member_stat = getMemberStatData(member_stat_dict, member)
        shared_point = share_dict[member]

        member_stat.committed_issue_count += 1
        member_stat.committed += shared_point

        if member_stat.max_committed_issue_point < shared_point:
            member_stat.max_committed_issue_point = shared_point

        if is_resolved:
            member_stat.resolved_issue_count += 1
            member_stat.finished += shared_point

            if member_stat.max_resolved_issue_point < shared_point:
                member_stat.max_resolved_issue_point = shared_point


# calculate story point share by "winner-gets-all" pattern
# developer > tester > other
def winnerGetsAll(contribution, story_point, developer_list, tester_list):
    share_dict = {}
    winners = []
    max = 0

    for member in list(contribution):
        if contribution[member] < max:
            continue
        else:
            if contribution[member] > max:
                max = contribution[member]
                winners = []

            winners.append(member)

    if len(winners) > 1:
        winners = list(
            filter(lambda i: i in developer_list or i in tester_list, winners))

    if len(winners) > 1:
        winners = list(filter(lambda i: i in developer_list, winners))

    for member in winners:
        share_dict[member] = story_point / len(winners)

    return share_dict


# share the story point by logged time percentage
def shareByLoggedTime(contribution, story_point, developer_list, tester_list):
    share_dict = {}
    member_list = contribution.keys()

    if len(member_list) > 1:
        member_list = filter(lambda i: i in developer_list or i in tester_list,
                             member_list)

    if len(member_list) > 1:
        member_list = filter(lambda i: i in developer_list, member_list)

    total_logged_time = 0
    for member in member_list:
        total_logged_time += contribution[member]
        share_dict[member] = contribution[member]

    for name in list(share_dict):
        share_dict[name] = share_dict[name] / total_logged_time * story_point

    return share_dict


# accumulate data from new feature issue
def handlePrimeryIssue(primary_issue, start_date, end_date, team_stat,
                       member_stat_dict):
    handleIssueWorkLogs(primary_issue.work_logs, primary_issue.type,
                        start_date, end_date, team_stat, member_stat_dict)

    for sub_issue in primary_issue.sub_issues:

        if sub_issue.type == 'Sprint Bug':
            primary_issue.dev_bug_count += 1

            if sub_issue.reporter != '':
                getMemberStatData(member_stat_dict,
                                  sub_issue.reporter).report_dev_bug += 1

            if sub_issue.labels is not None and len(sub_issue.labels) > 0:
                bug_label = sub_issue.labels[0]

                if bug_label not in team_stat.dev_bug_sum:
                    team_stat.dev_bug_sum[bug_label] = 0

                team_stat.dev_bug_sum[bug_label] += 1

        handleIssueWorkLogs(sub_issue.work_logs, sub_issue.type, start_date,
                            end_date, team_stat, member_stat_dict)


def handleIssueWorkLogs(work_logs, issue_type, start_date, end_date, team_stat,
                        member_stat_dict):
    for log in work_logs:
        if matchDateRangeLimit(log['created'], start_date, end_date) == False:
            continue

        logged_time = log['timeSpentSeconds']
        member_name = log['author']['displayName']

        if issue_type == 'Sprint Bug':
            team_stat.logged_time_dev_bug += logged_time
            getMemberStatData(member_stat_dict,
                              member_name).logged_time_dev_bug += logged_time

        elif issue_type in ['Test Case', 'Sub Test Execution', 'Test Plan']:
            team_stat.logged_time_testing += logged_time
            getMemberStatData(member_stat_dict,
                              member_name).logged_time_testing += logged_time

        elif issue_type == 'Bug':
            team_stat.logged_time_existing_bug += logged_time
            getMemberStatData(
                member_stat_dict,
                member_name).logged_time_existing_bug += logged_time

        else:
            # include sprint task and others
            team_stat.logged_time_new_feature += logged_time
            getMemberStatData(
                member_stat_dict,
                member_name).logged_time_new_feature += logged_time
