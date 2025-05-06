import jiradata.data_service as JiraData
from cache.CacheService import cache_service

default_ttl = 60 * 60 * 24 * 30

class JiraDataService:
    @cache_service.cache(ttl=default_ttl)
    def get_boards(self, type='scrum', start_at=0):
        return JiraData.getBoards(type, start_at)

    @cache_service.cache(ttl=default_ttl)
    def get_sprints_for_board(self, board_id, start_at=0):
        return JiraData.getSprintsForBoard(board_id, start_at)
    
    @cache_service.cache(ttl=default_ttl)
    def get_issues_for_sprint(self, sprint_id, start_at=0):
        return JiraData.getIssuesForSprint(sprint_id, start_at)

    @cache_service.cache(ttl=default_ttl)
    def get_sprint_report(self, board_id, sprint_id):
        return JiraData.getSprintReportInfo(board_id, sprint_id)
    
    @cache_service.cache(ttl=default_ttl)
    def get_sprint_info(self, sprint_id):
        return JiraData.getSprintInfo(sprint_id)

jira_service = JiraDataService()
