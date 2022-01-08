import csv
import jiradata.data_service as data
import jiradata.data_process as process

from datetime import timedelta
from dateutil import parser


def kanbanOverview():
    pass


def sprintOvewview():
    pass


def sprintDetailView(sprint_id):
    pass


def checkIfLoggedWithinRange(log_list, start, end):
    for log in log_list:
        logged_datetime = parser(log['created'])

    return False


def getPeriodRelatedIssues(issue_list, period_start, period_end):
    related_issues = []

    for id in list(issue_list):
        issue_data = issue_list[id]
        resolution_date = parser(issue_data.resolution_date)

        if resolution_date >= period_start and resolution_date <= period_end:
            related_issues.append(issue_data)
        else:
            for sub_issue_data in issue_data.sub_issues:
                pass


def periodIssueOvewview(issue_list, period_start, period_end):
    related_issues = []


def sprintReport1(sprint_id):
    sprint_issues = data.getSprintIssues(sprint_id)
    sprint_issue_stat = process.process_issue_list(sprint_issues)

    pass


def prepareKanbanReportData(board_id, period_start, review_period,
                            period_count):
    board_info = data.getBoardInfo(board_id)
    board_issues = data.getBoardIssues(board_id)

    period_stat_list = []
    primary_issue_summary = process.process_issue_list(board_issues)

    # Iterate periods
    for i in range(period_count):
        period_end = period_start + timedelta(days=review_period)

        period_stat_list.append(
            process.summarize_kanban_stat(primary_issue_summary, period_start,
                                          period_end))

        period_start = period_end

    return {
        'board_info': board_info,
        'primary_issue_summary': primary_issue_summary,
        'period_stat_list': period_stat_list
    }


def exportKanbanReport(board_id,
                       start_date_str,
                       review_period=7,
                       period_count=2):
    start_date = parser.parse(start_date_str)
    end_date = start_date + timedelta(days=review_period * period_count)

    result = prepareKanbanReportData(board_id, start_date, review_period,
                                     period_count)

    board_info = result['board_info']
    primary_issue_summary = result['primary_issue_summary']
    period_stat_list = result['period_stat_list']

    review_period_desc = start_date.strftime(
        '%b-%d-%Y') + ' ~ ' + end_date.strftime('%b-%d-%Y')
    outputFilename = 'output/kanban-overview (' + review_period_desc + ').csv'

    with open(outputFilename, mode='w', newline='') as report_file:
        report_writter = csv.writer(report_file,
                                    delimiter=',',
                                    quotechar='"',
                                    quoting=csv.QUOTE_MINIMAL)

        report_writter.writerow(['Kanban Name:', board_info['name']])
        report_writter.writerow(['Review Period:', review_period_desc])
        report_writter.writerow([])

        for period_stat in period_stat_list:
            team_total_logged = (period_stat.logged_time_new_feature +
                                 period_stat.logged_time_dev_bug +
                                 period_stat.logged_time_existing_bug +
                                 period_stat.logged_time_testing)

            # print team stat
            report_writter.writerow(['Period:', period_stat.name])
            report_writter.writerow(['Completed:', period_stat.finished])
            report_writter.writerow(
                ['Total Hours Logged:',
                 round(team_total_logged / 60 / 60, 1)])
            report_writter.writerow([
                'New Feature Development:',
                displayPercentage(period_stat.logged_time_new_feature,
                                  team_total_logged)
            ])
            report_writter.writerow([
                'Development Bugs:',
                displayPercentage(period_stat.logged_time_dev_bug,
                                  team_total_logged)
            ])
            report_writter.writerow([
                'Existing Bugs:',
                displayPercentage(period_stat.logged_time_existing_bug,
                                  team_total_logged)
            ])
            report_writter.writerow([
                'New Feature Testing:',
                displayPercentage(period_stat.logged_time_testing,
                                  team_total_logged)
            ])

            report_writter.writerow([])
            report_writter.writerow([])

            # print team member stat
            report_writter.writerow(['Member Overview:'])
            report_writter.writerow([
                'Member', 'Total Hours Logged', 'Finished Count',
                'Finished Point', 'Avg. Finished Point',
                'Max Single Finished Point', 'Finished Contribution',
                'Fix Existing Bug Count'
            ])

            report_writter.writerow([])
            report_writter.writerow([])

            for name in list(period_stat.member_stat_summary):
                member_stat = period_stat.member_stat_summary[name]
                member_total_logged = (member_stat.logged_time_new_feature +
                                       member_stat.logged_time_dev_bug +
                                       member_stat.logged_time_existing_bug +
                                       member_stat.logged_time_testing)

                report_writter.writerow([
                    name,
                    round(member_total_logged / 60 / 60, 1),
                    member_stat.resolved_issue_count, member_stat.finished,
                    0 if member_stat.resolved_issue_count <= 0 else round(
                        member_stat.finished /
                        member_stat.resolved_issue_count, 2),
                    member_stat.max_issue_point,
                    displayPercentage(member_stat.finished,
                                      period_stat.finished),
                    member_stat.fixed_bug
                ])

            report_writter.writerow([])
            report_writter.writerow([])

        all_contributors = []
        for key in list(primary_issue_summary):
            for name in primary_issue_summary[key].contributors:
                if name not in all_contributors:
                    all_contributors.append(name)

        # print team primary issue stat
        report_writter.writerow(['Primary Issue Overview:'])
        report_writter.writerow([
            'Issue Key', 'Issue Type', 'Story Point', 'Main Contributor',
            'Resolved', 'Resolved Date'
        ] + all_contributors)

        for id in list(primary_issue_summary):
            issue_data = primary_issue_summary[id]
            is_resolved = issue_data.resolution_date is not None and issue_data.resolution_date != ''

            member_contribution = []

            for name in all_contributors:
                if name in issue_data.contributors:
                    member_contribution.append(
                        round(issue_data.contributors[name] / 60 / 60, 1))
                else:
                    member_contribution.append(0)

            report_writter.writerow([
                issue_data.key, issue_data.type, issue_data.story_point,
                issue_data.main_contributor, 1 if is_resolved else 0,
                issue_data.resolution_date
            ] + member_contribution)

        report_writter.writerow([])
        report_writter.writerow([])

    print('Kanban Report Export Successfully.')


def displayPercentage(numerator, denominator):
    return str(100 * (numerator / denominator)) + "%" if denominator > 0 else 0
