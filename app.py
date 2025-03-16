from flask import Flask, request, jsonify
from flask_cors import CORS
import jiradata.data_service as JiraData
from jiradata.data_model import SprintSummary, JiraIssue

app = Flask(__name__)
CORS(app)


@app.route('/get-sprint-data', methods=['GET'])
def get_sprint_data():
    sprint_id = request.args.get('sprintId')

    if not sprint_id:
        return jsonify({'error': 'Sprint Id is required'}), 400

    sprint_data = JiraData.getSprintInfo(sprint_id)

    if sprint_data:
        return jsonify(sprint_data)
    else:
        return jsonify({'error': 'Failed to fetch sprint data'}), 500


@app.route('/get-boards', methods=['GET'])
def get_boards():
    board_list = JiraData.getBoards()

    if board_list:
        return jsonify(board_list)
    else:
        return jsonify({'error': 'Failed to fetch boards data'}), 500


@app.route('/get-board-sprints', methods=['GET'])
def get_board_sprints():
    board_id = request.args.get('boardId')

    if not board_id:
        return jsonify({'error': 'Board Id is required'}), 400

    sprints_data = JiraData.getSprintsForBoard(board_id)

    if sprints_data:
        return jsonify(sprints_data)
    else:
        return jsonify({'error': 'Failed to fetch sprints'}), 500


@app.route('/get-sprint-issues', methods=['GET'])
def get_sprint_issues():
    sprint_id = request.args.get('sprintId')

    if not sprint_id:
        return jsonify({'error': 'Sprint Id is required'}), 400

    issues_data = JiraData.getIssuesForSprint(sprint_id)

    if issues_data:
        return jsonify(issues_data)
    else:
        return jsonify({'error': 'Failed to fetch issues'}), 500


if __name__ == '__main__':
    app.run(debug=True)
