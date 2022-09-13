import jiradata.data_overview as overview

# export report for sprint as csv
# parameters: sprint id, team name, share point pattern
overview.exportSprintReport(1659, 'Team 3', 2)

# export spring time logs
# overview.exportSprintTimeLog(1659, ['RW-33181', 'RW-31702', 'RW-32880'])