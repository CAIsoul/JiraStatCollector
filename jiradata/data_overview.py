import csv
import re
import jiradata.data_service as data
import jiradata.data_process as process
from jiradata.data_model import WorkLogInfo

from datetime import timedelta
from dateutil import parser

team_info = {
    'Team 2': {
        'developer': [
            'Zhipeng (David) Xie',
            'Paul Huang',
            'Howard Wu',
            'Zhiguo (Ronel) Wu',
        ],
        'tester': [
            'Manman (Mancy) Xu',
        ]
    },
    'Team 3': {
        'developer': [
            'Jiangyi (Sailias) Peng',
            'Hantian (Tom) Wu',
            'Wei (Nate) Shi',
            'Jiaqi Cai',
        ],
        'tester': [
            'Weiying (Amy) Shi',
        ]
    },
    'Team 4': {
        'developer': [
            'Xihong (Scott) Shi',
            'Wei (Will) Xiao',
            'Chenjie (Leo) Deng',
            'Lianbo Lu',
        ],
        'tester': [
            'Zhihong (Kevin) Chen',
        ]
    },
    'Team 6': {
        'developer': [
            'Qingjiao (Cary) Liu',
            'Guoqing (Dong) Dong',
            'Jie (Albin) Xi',
            'Hugh Zhang',
            'Min Hong',
        ],
        'tester': [
            'Wei (Vivian) Zhang',
        ]
    },
    'Team 7': {
        'developer': [
            'Kai (Ted) Li',
            'Zhan (Sam) Shi',
            'Min Li',
            'Xu (Sara) Chu',
        ],
        'tester': [
            'Xiaochun (Spring) Liu',
        ]
    },
}


def prepareKanbanReportData(board_id, period_start, review_period,
                            period_count):
    board_info = data.getBoardInfo(board_id)
    board_issues = data.getBoardIssues(board_id)

    period_stat_list = []
    primary_issue_summary = process.process_issue_list(board_issues)

    # Iterate periods
    for i in range(period_count):
        period_end = period_start + timedelta(days=review_period)

        team_stat = process.summarize_kanban_stat(primary_issue_summary,
                                                  period_start, period_end)

        team_stat.name = period_start.strftime(
            '%b/%d/%Y') + ' ~ ' + period_end.strftime('%b/%d/%Y')

        period_stat_list.append(team_stat)

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
                    member_stat.max_resolved_issue_point,
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

        # print team primary issue stat'
        report_writter.writerow([])
        report_writter.writerow([])

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


def exportSprintReport(sprint_id, team, share_pattern=1):
    sprint_info = data.getSprintInfo(sprint_id)
    sprint_issues = data.getSprintIssuesViaRequest(sprint_id)

    primary_issue_summary = process.process_issue_list(sprint_issues)

    start_date = parser.parse(sprint_info['startDate'])
    end_date = parser.parse(sprint_info['endDate'])

    sprint_stat = process.summarize_sprint_stat(primary_issue_summary,
                                                start_date, end_date,
                                                team_info[team]['developer'],
                                                team_info[team]['tester'],
                                                share_pattern)

    outputFilename = 'output/sprint-overview (' + (re.sub(
        '/', '-', sprint_info['name'])) + ').csv'

    with open(outputFilename, mode='w', newline='') as review_file:
        summary_writter = csv.writer(review_file,
                                     delimiter=',',
                                     quotechar='"',
                                     quoting=csv.QUOTE_MINIMAL)

        summary_writter.writerow([sprint_info['name']])
        summary_writter.writerow([])

        summary_writter.writerow(['Sprint Overview:'])
        summary_writter.writerow([
            'Completed/Committed:',
            str(sprint_stat.finished) + '/' + str(sprint_stat.committed)
        ])
        summary_writter.writerow([
            'Total Hours Logged:',
            round(sprint_stat.logged_time_total / 60 / 60, 1)
        ])
        summary_writter.writerow([
            'New Feature Development:',
            str(100 * (sprint_stat.logged_time_new_feature /
                       sprint_stat.logged_time_total)) +
            "%" if sprint_stat.logged_time_total > 0 else 0
        ])
        summary_writter.writerow([
            'Development Bugs:',
            str(100 * (sprint_stat.logged_time_dev_bug /
                       sprint_stat.logged_time_total)) +
            "%" if sprint_stat.logged_time_total > 0 else 0
        ])
        summary_writter.writerow([
            'Existing Bugs:',
            str(100 * (sprint_stat.logged_time_existing_bug /
                       sprint_stat.logged_time_total)) +
            "%" if sprint_stat.logged_time_total > 0 else 0
        ])
        summary_writter.writerow([
            'New Feature Testing:',
            str(100 * (sprint_stat.logged_time_testing /
                       sprint_stat.logged_time_total)) +
            "%" if sprint_stat.logged_time_total > 0 else 0
        ])

        summary_writter.writerow([])
        summary_writter.writerow([])

        summary_writter.writerow(['Dev Bug Overview:'])
        for category in list(sprint_stat.dev_bug_sum):
            summary_writter.writerow(
                [category, sprint_stat.dev_bug_sum[category]])

        summary_writter.writerow([])
        summary_writter.writerow([])

        summary_writter.writerow(['Member Overview:'])
        summary_writter.writerow([
            'Member',
            'Total Hours Logged',
            'Assigned Count',
            'Assigned Point',
            'Avg. Assigned Point',
            'Max Single Assigned Point',
            'Assigned Contribution',
            'Finished Count',
            'Finished Point',
            'Avg. Finished Point',
            'Max Single Finished Point',
            'Finished Contribution',
            'Fix Existing Bug Count',
            'Completeness',
            'Reported Dev Bug Count',
        ])

        for name in list(sprint_stat.member_stat_summary):
            member_stat = sprint_stat.member_stat_summary[name]
            member_total_logged = (member_stat.logged_time_new_feature +
                                   member_stat.logged_time_dev_bug +
                                   member_stat.logged_time_existing_bug +
                                   member_stat.logged_time_testing)

            summary_writter.writerow([
                name,
                round(member_total_logged / 60 / 60, 1),
                member_stat.committed_issue_count,
                round(member_stat.committed, 1),
                0 if member_stat.committed_issue_count <= 0 else round(
                    member_stat.committed /
                    member_stat.committed_issue_count, 2),
                member_stat.max_committed_issue_point,
                str(100 * (member_stat.committed / sprint_stat.committed)) +
                "%" if sprint_stat.committed > 0 else 0,
                member_stat.resolved_issue_count,
                round(member_stat.finished, 1),
                0 if sprint_stat.committed <= 0 else round(
                    member_stat.finished / sprint_stat.finished, 2),
                member_stat.max_resolved_issue_point,
                str(100 * (member_stat.finished / sprint_stat.finished)) +
                "%" if sprint_stat.finished > 0 else 0,
                member_stat.fixed_bug,
                str(100 * (member_stat.finished / member_stat.committed)) +
                "%" if member_stat.committed > 0 else 0,
                member_stat.report_dev_bug,
            ])

        all_contributors = []
        for key in list(primary_issue_summary):
            for name in primary_issue_summary[key].contributors:
                if name not in all_contributors:
                    all_contributors.append(name)

        # print team primary issue stat
        summary_writter.writerow(['Primary Issue Overview:'])
        summary_writter.writerow([
            'Issue Key',
            'Issue Type',
            'Story Point',
            'Main Contributor',
            'Resolved',
            'Resolved Date',
            'Dev Bug Count',
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

            summary_writter.writerow([
                issue_data.key,
                issue_data.type,
                issue_data.story_point,
                issue_data.main_contributor,
                1 if is_resolved else 0,
                issue_data.resolution_date,
                issue_data.dev_bug_count,
            ] + member_contribution)

    print('Sprint Overview Exported.')


def exportSprintTimeLog(sprint_id):
    info = data.getSprintInfo(sprint_id)
    issues = data.getSprintIssuesViaRequest(sprint_id)

    start_date = parser.parse(info['startDate'])
    end_date = parser.parse(info['endDate'])

    work_log_summary = process.summarizedSprintWorkLogs(
        issues, start_date, end_date)

    outputFilename = 'output/sprint-work-log (' + (re.sub(
        '/', '-', info['name'])) + ').csv'

    with open(outputFilename, mode='w', newline='') as report_file:
        report_writter = csv.writer(report_file,
                                    delimiter=',',
                                    quotechar='"',
                                    quoting=csv.QUOTE_MINIMAL)
        report_writter.writerow(['Work Log Report:', info['name']])
        report_writter.writerow(
            ['Date', 'Member', 'JIRA Issue', 'Logged Hour(s)'])

        sprint_days = (end_date - start_date).days

        for i in range(sprint_days):
            this_date = start_date + timedelta(days=i)
            date_str = this_date.strftime('%b/%d/%Y')

            if i not in work_log_summary:
                report_writter.writerow([date_str])
                report_writter.writerow([])
                report_writter.writerow([])
                continue

            log_list = work_log_summary[i]
            log_list = sorted(log_list, key=lambda x: x.member)

            for index, log in enumerate(log_list):
                first_column = date_str if index == 0 else ''
                log_values = [
                    first_column, log.member, log.issueKey,
                    round(log.duration / 60 / 60, 1)
                ]

                report_writter.writerow(log_values)

            report_writter.writerow([])
            report_writter.writerow([])

    print('Sprint Log Report Exported.')
