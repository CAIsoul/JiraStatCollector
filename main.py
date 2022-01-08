import configparser
from jiradata.data_overview import exportKanbanReport

# export report for kanban
exportKanbanReport(49, '2021-12-17T00:00:00.000+0800', 7, 3)

# export report for sprint
# exportSprintReport(1482)