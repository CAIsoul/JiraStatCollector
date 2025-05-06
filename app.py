from flask import Flask, request, jsonify
from flask_cors import CORS
from jiradata.DataService import jira_service

app = Flask(__name__)
CORS(app)


@app.route('/get-sprint-data', methods=['GET'])
def get_sprint_data():
    sprint_id = request.args.get('sprintId')

    if not sprint_id:
        return jsonify({'error': 'Sprint Id is required'}), 400

    sprint_data = jira_service.get_sprint_info(sprint_id)

    if sprint_data:
        return jsonify(sprint_data)
    else:
        return jsonify({'error': 'Failed to fetch sprint data'}), 500


@app.route('/get-boards', methods=['GET'])
def get_boards():
    board_type = request.args.get('type')

    board_list = jira_service.get_boards(board_type)

    if board_list:
        return jsonify(board_list)
    else:
        return jsonify({'error': 'Failed to fetch boards data'}), 500


@app.route('/get-board-sprints', methods=['GET'])
def get_board_sprints():
    board_id = request.args.get('boardId')

    if not board_id:
        return jsonify({'error': 'Board Id is required'}), 400

    sprints_data = jira_service.get_sprints_for_board(board_id)

    if sprints_data:
        return jsonify(sprints_data)
    else:
        return jsonify({'error': 'Failed to fetch sprints'}), 500


@app.route('/get-sprint-issues', methods=['GET'])
def get_sprint_issues():
    sprint_id = request.args.get('sprintId')

    if not sprint_id:
        return jsonify({'error': 'Sprint Id is required'}), 400

    issues_data = jira_service.get_issues_for_sprint(sprint_id)

    if issues_data:
        return jsonify(issues_data)
    else:
        return jsonify({'error': 'Failed to fetch issues'}), 500


@app.route('/get-sprint-report', methods=['GET'])
def get_sprint_report():
    sprint_id = request.args.get('sprintId')
    board_id = request.args.get('boardId')

    if not board_id:
        return jsonify({'error': 'Board Id is required'}), 400

    if not sprint_id:
        return jsonify({'error': 'Sprint Id is required'}), 400

    sprint_report = jira_service.get_sprint_report(board_id, sprint_id)

    if sprint_report:
        return jsonify(sprint_report)
    else:
        return jsonify({'error': 'Fail to fetch sprint report'}), 500


if __name__ == '__main__':
    app.run(debug=True)
