from datetime import timedelta
from dateutil import parser
from jiradata.data_model import JiraIssue, TeamStat, MemberStat

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
def summarize_sprint_stat(primary_issue_summary, sprint_start, sprint_end):
    team_stat = TeamStat()
    member_stat_dict = {}

    for id in list(primary_issue_summary):
        issue_data = primary_issue_summary[id]

        calculateMainContributor(issue_data, sprint_start, sprint_end)

        accumulateStatForPrimaryIssue(issue_data, team_stat, member_stat_dict,
                                      sprint_start, sprint_start)

    team_stat.member_stat_summary = member_stat_dict

    return team_stat


#summarize kanban stat
def summarize_kanban_stat(primary_issue_summary, review_start, review_end):
    team_stat = TeamStat()
    member_stat_dict = {}

    team_stat.name = review_start.strftime(
        '%b/%d/%Y') + ' ~ ' + review_end.strftime('%b/%d/%Y')

    for id in list(primary_issue_summary):
        issue_data = primary_issue_summary[id]

        calculateMainContributor(issue_data)

        accumulateStatForPrimaryIssue(issue_data, team_stat, member_stat_dict,
                                      review_start, review_end)

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
                or end_date is not None and date > end_date) == False

    return True


# accumulate stat from primary issues (including sub-issues)
def accumulateStatForPrimaryIssue(issue_data,
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

            if (main_contributor_stat.max_issue_point <= 0
                    or issue_data.story_point >
                    main_contributor_stat.max_issue_point):
                main_contributor_stat.max_issue_point = issue_data.story_point

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

    winner = ''
    for name in list(contributor_summary):
        if winner == '' or contributor_summary[name] > contributor_summary[
                winner]:
            winner = name

    primary_issue.main_contributor = winner
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
