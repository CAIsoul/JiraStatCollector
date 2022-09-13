import jiradata.data_overview as overview

# board enum
# Plus - 53
# SF - 13
# PAT - 99

# export report for sprint as csv
# parameters: board id, sprint id, team name, share point pattern
overview.exportSprintReport(99, 1646, 'R&D', 2)

# export spring time logs
# overview.exportSprintTimeLog(1606)