import csv
import re
import jiradata.data_service as data
import jiradata.data_process as process
from jiradata.data_model import WorkLogInfo, SprintSummary

from datetime import timedelta
from dateutil import parser

team_info = {
    'R&D': {
        'developer': [
            'Chen Li',
            'Wei (Nate) Shi',
            'Juntao (Steven) Cheng',
            'Yue (Mina) Zhang',
        ],
        'tester': []
    },
    'Team 2': {
        'developer': [
            'Zhipeng (David) Xie',
            'Paul Huang',
            'Howard Wu',
            'Zhiguo (Ronel) Wu',
        ],
        'tester': []
    },
    'Team 3': {
        'developer': [
            'Jiangyi (Sailias) Peng',
            'Hantian (Tom) Wu',
            'Wei (Nate) Shi',
            'Jiaqi Cai',
            'Zhe (Jack) Wang',
            'Yi (Vitale) Zhou',
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
            'Haikuo Pan',
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
            'Lu (Luke) Jian',
            'Lei Li',
        ],
        'tester': [
            'Feng (Fred) Zhou',
        ]
    },
}


def displayPercentage(numerator, denominator):
    return str(100 * (numerator / denominator)) + "%" if denominator > 0 else 0


def exportSprintStat(sprint_id, team, rollover_issue_keys=[], share_pattern=1):
    sprint_issue_dict = data.getSprintIssueDict(sprint_id)
    sprint_report = data.getSprintReportInfo(sprint_id)
    sprint_info = SprintSummary(sprint_report)

    start_date = sprint_info.start_date
    end_date = sprint_info.end_date + timedelta(days=1)

    sprint_stat = process.summarize_sprint_stat(sprint_issue_dict, start_date,
                                                end_date,
                                                team_info[team]['developer'],
                                                team_info[team]['tester'],
                                                share_pattern)

    sprint_stat.sprint_info = sprint_info
    sprint_stat.primary_issue_summary = sprint_issue_dict

    return sprint_stat


def exportSprintReport(sprint_id,
                       team,
                       rollover_issue_keys=[],
                       share_pattern=1):

    sprint_stat = exportSprintStat(sprint_id, team, rollover_issue_keys,
                                   share_pattern)

    sprint_info = sprint_stat.sprint_info
    primary_issue_summary = sprint_stat.primary_issue_summary

    outputFilename = 'output/sprint-overview (' + (re.sub(
        '/', '-', sprint_info.name)) + ').csv'

    with open(outputFilename, mode='w', newline='') as review_file:
        summary_writter = csv.writer(review_file,
                                     delimiter=',',
                                     quotechar='"',
                                     quoting=csv.QUOTE_MINIMAL)

        summary_writter.writerow([sprint_info.name])
        summary_writter.writerow([])

        summary_writter.writerow(['Sprint Overview:'])
        summary_writter.writerow([
            'Original Committed:',
            str(sprint_info.original_completed_point +
                sprint_info.original_not_completed_point +
                sprint_info.original_removed_point)
        ])
        summary_writter.writerow(
            ['Original Completed:',
             str(sprint_info.original_completed_point)])
        summary_writter.writerow([
            'Original Not Completed:',
            str(sprint_info.original_not_completed_point)
        ])
        summary_writter.writerow(
            ['Original Removed:',
             str(sprint_info.original_removed_point)])
        summary_writter.writerow([
            'Newly Added:',
            str(sprint_info.new_completed_point +
                sprint_info.new_not_completed_point)
        ])
        summary_writter.writerow(
            ['Newly Added Completed:',
             str(sprint_info.new_completed_point)])
        summary_writter.writerow([
            'Newly Added Not Completed:',
            str(sprint_info.new_not_completed_point)
        ])
        summary_writter.writerow([
            'Total Committed:',
            str(sprint_info.original_completed_point +
                sprint_info.original_not_completed_point +
                sprint_info.original_removed_point +
                sprint_info.new_completed_point +
                sprint_info.new_not_completed_point)
        ])
        summary_writter.writerow([
            'Total Completed:',
            str(sprint_info.original_completed_point +
                sprint_info.new_completed_point)
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
            'Completed Count',
            'Completed Point',
            'Avg. Completed Point',
            'Max Single Completed Point',
            'Completed Contribution',
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
                round(member_stat.completed, 1),
                0 if sprint_stat.completed <= 0 else round(
                    member_stat.completed / sprint_stat.completed, 2),
                member_stat.max_resolved_issue_point,
                str(100 * (member_stat.completed / sprint_stat.completed)) +
                "%" if sprint_stat.completed > 0 else 0,
                member_stat.fixed_bug,
                str(100 * (member_stat.completed / member_stat.committed)) +
                "%" if member_stat.committed > 0 else 0,
                member_stat.report_dev_bug,
            ])

        all_contributors = []
        for key in list(primary_issue_summary):
            for name in primary_issue_summary[key].contributors:
                if name not in all_contributors:
                    all_contributors.append(name)

        summary_writter.writerow([])
        summary_writter.writerow([])

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
    issues = data.getIssuesBySprintId(sprint_id)

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
