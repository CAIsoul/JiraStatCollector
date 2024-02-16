import jiradata.data_overview as overview

# # export report for sprint as csv
# # parameters: sprint id, team name, share point pattern
# overview.exportSprintReport(2008, 99, ['TFSH3', 'TFSH9'], 2)

# # export spring time logs
overview.exportMemberWorklogReport(2008, ['TFSH3', 'TFSH9'])
