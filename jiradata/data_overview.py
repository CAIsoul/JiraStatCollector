import csv
import re
import os
import pytz
import configparser
import jiradata.data_service as data
import jiradata.data_process as process
from jiradata.data_model import SprintSummary

from datetime import timedelta
from dateutil import parser

config = configparser.ConfigParser()
configFilePath = os.path.join(os.path.dirname(__file__) + r'/../app.ini')
config.read(configFilePath, encoding='utf-8')

TIMEZONE_OFFSET = config.get('TimeZone', 'OFFSET')
TIMEZONE_OFFSET = 0 if TIMEZONE_OFFSET == '' else int(TIMEZONE_OFFSET)

team_info = {
    'R&D': {
        'developer': [
            'Chen Li',
            'Wei (Nate) Shi',
            'Juntao (Steven) Cheng',
            'Chenjie (Leo) Deng',
            'Jiangyi (Sailias) Peng',
        ],
        'tester': []
    },
    'Team 1': {
        'developer': [
            'Zhiguo (Ronel) Wu',
            'Xiong (Bear) Xu',
            'Damon Huang',
            'Hong (Jane) Zhou',
            'Adrain Xue',
        ],
        'tester': [
            'Hanwei (Susan) Mao',
        ]
    },
    'Team 2': {
        'developer': [
            'Zhipeng (David) Xie',
            'Paul Huang',
            'Howard Wu',
            'Fan (Jason) Zhu',
            'Gang (Shawn) Huang',
        ],
        'tester': ['Nan (Murphy) Cheng']
    },
    'Team 3': {
        'developer': [
            'Xiao (Aaron) Zhou',
            'Hantian (Tom) Wu',
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
            'Lianbo Lu',
            'Haikuo Pan',
            'Dongjun (Frank) Xing',
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


def exportSprintStat(sprint_id, team, share_pattern=1):
    sprint_info = data.getSprintInfo(sprint_id)
    board_id = sprint_info["originBoardId"]

    sprint_issue_dict = data.getSprintIssueDict(sprint_id)
    sprint_report = data.getSprintReportInfo(board_id, sprint_id)

    sprint_summary = SprintSummary(sprint_report)

    start_date = sprint_summary.start_date - timedelta(days=1)
    end_date = sprint_summary.end_date + timedelta(days=1)

    team_stat = process.summarize_team_stat(sprint_issue_dict, start_date,
                                            end_date,
                                            team_info[team]['developer'],
                                            team_info[team]['tester'],
                                            share_pattern)

    sprint_summary.primary_issues = sprint_issue_dict
    sprint_summary.team_stat = team_stat

    return sprint_summary


def exportSprintReport(sprint_id, team, share_pattern=1):

    sprint_summary = exportSprintStat(sprint_id, team, share_pattern)

    primary_issue_summary = sprint_summary.primary_issues
    team_stat = sprint_summary.team_stat

    outputFilename = 'output/sprint-overview (' + (re.sub(
        '/', '-', sprint_summary.name)) + ').csv'

    with open(outputFilename, mode='w', newline='') as review_file:
        summary_writter = csv.writer(review_file,
                                     delimiter=',',
                                     quotechar='"',
                                     quoting=csv.QUOTE_MINIMAL)

        summary_writter.writerow([sprint_summary.name])
        summary_writter.writerow([])

        summary_writter.writerow(['Sprint Overview:'])
        summary_writter.writerow([
            'Original Committed:',
            str(sprint_summary.original_completed_point +
                sprint_summary.original_not_completed_point +
                sprint_summary.original_removed_point)
        ])
        summary_writter.writerow([
            'Original Completed:',
            str(sprint_summary.original_completed_point)
        ])
        summary_writter.writerow([
            'Original Not Completed:',
            str(sprint_summary.original_not_completed_point)
        ])
        summary_writter.writerow(
            ['Original Removed:',
             str(sprint_summary.original_removed_point)])
        summary_writter.writerow([
            'Newly Added:',
            str(sprint_summary.new_completed_point +
                sprint_summary.new_not_completed_point)
        ])
        summary_writter.writerow([
            'Newly Added Completed:',
            str(sprint_summary.new_completed_point)
        ])
        summary_writter.writerow([
            'Newly Added Not Completed:',
            str(sprint_summary.new_not_completed_point)
        ])
        summary_writter.writerow([
            'Total Committed:',
            str(sprint_summary.original_completed_point +
                sprint_summary.original_not_completed_point +
                sprint_summary.original_removed_point +
                sprint_summary.new_completed_point +
                sprint_summary.new_not_completed_point)
        ])
        summary_writter.writerow([
            'Total Completed:',
            str(sprint_summary.original_completed_point +
                sprint_summary.new_completed_point)
        ])
        summary_writter.writerow([
            'Total Hours Logged:',
            round(team_stat.logged_time_total / 60 / 60, 1)
        ])
        summary_writter.writerow([
            'New Feature Development:',
            str(100 * (team_stat.logged_time_new_feature /
                       team_stat.logged_time_total)) +
            "%" if team_stat.logged_time_total > 0 else 0
        ])
        summary_writter.writerow([
            'Development Bugs:',
            str(100 *
                (team_stat.logged_time_dev_bug / team_stat.logged_time_total))
            + "%" if team_stat.logged_time_total > 0 else 0
        ])
        summary_writter.writerow([
            'Existing Bugs:',
            str(100 * (team_stat.logged_time_existing_bug /
                       team_stat.logged_time_total)) +
            "%" if team_stat.logged_time_total > 0 else 0
        ])
        summary_writter.writerow([
            'New Feature Testing:',
            str(100 *
                (team_stat.logged_time_testing / team_stat.logged_time_total))
            + "%" if team_stat.logged_time_total > 0 else 0
        ])

        summary_writter.writerow([])
        summary_writter.writerow([])

        summary_writter.writerow(['Dev Bug Overview:'])
        for category in list(team_stat.dev_bug_sum):
            summary_writter.writerow(
                [category, team_stat.dev_bug_sum[category]])

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

        for name in list(team_stat.member_stat_summary):
            member_stat = team_stat.member_stat_summary[name]
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
                str(100 * (member_stat.committed / team_stat.committed)) +
                "%" if team_stat.committed > 0 else 0,
                member_stat.resolved_issue_count,
                round(member_stat.completed, 1),
                0 if team_stat.completed <= 0 else round(
                    member_stat.completed / team_stat.completed, 2),
                member_stat.max_resolved_issue_point,
                str(100 * (member_stat.completed / team_stat.completed)) +
                "%" if team_stat.completed > 0 else 0,
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


def exportSprintTimeLog(sprint_id, extra_issues):
    sprint_info = data.getSprintInfo(sprint_id)
    issues = data.getIssuesBySprintId(sprint_id)

    if extra_issues is not None and len(extra_issues) > 0:
        issues += data.getIssuesByKeys(extra_issues)

    # from timezone navie to aware
    timezone = pytz.FixedOffset(TIMEZONE_OFFSET)
    start_date = parser.parse(
        sprint_info['startDate']).replace(tzinfo=timezone)
    end_date = parser.parse(sprint_info['endDate']).replace(tzinfo=timezone)

    work_log_summary = process.summarizedSprintWorkLogs(
        issues, start_date, end_date)

    sprint_day_count = (end_date - start_date).days + 1

    outputFilename = 'output/sprint-work-log (' + (re.sub(
        '/', '-', sprint_info['name'])) + ').csv'

    with open(outputFilename, mode='w', newline='') as report_file:
        report_writter = csv.writer(report_file,
                                    delimiter=',',
                                    quotechar='"',
                                    quoting=csv.QUOTE_MINIMAL)
        report_writter.writerow(['Work Log Report:', sprint_info['name']])
        report_writter.writerow([
            'Period',
            start_date.strftime('%Y-%m-%d'),
            end_date.strftime('%Y-%m-%d')
        ])

        display_date_list = list(
            map(
                lambda x:
                (start_date + timedelta(days=x)).strftime('%b %d %a'),
                range(sprint_day_count)))
        report_writter.writerow(['Member\Date'] + display_date_list)

        for author in work_log_summary:
            max = 0
            total = {}

            for day in work_log_summary[author]:
                count = len(work_log_summary[author][day])
                max = max if count < max else count

            for i in range(max):
                print_cols = []
                first_col = author if i == 0 else ''
                print_cols.append(first_col)

                for j in range(sprint_day_count):
                    this_col = ''
                    if j in work_log_summary[author] and len(
                            work_log_summary[author][j]) > i:
                        log = work_log_summary[author][j][i]
                        logged_hour = log.duration / 60 / 60
                        this_col = '{} - {} hr(s) on {}'.format(
                            log.created.astimezone(timezone).strftime('%H:%M'),
                            round(logged_hour, 1), log.issue_key)

                        if j in total:
                            total[j] += logged_hour
                        else:
                            total[j] = logged_hour

                    print_cols.append(this_col)

                report_writter.writerow(print_cols)

            report_writter.writerow([])

            total_cols = ['Total:']
            for k in range(sprint_day_count):
                total_col = ''

                if k in total:
                    total_col = '{} hr(s)'.format(round(total[k], 1))

                total_cols.append(total_col)

            report_writter.writerow(total_cols)
            report_writter.writerow([])
            report_writter.writerow([])

    print('Sprint Log Report Exported.')
