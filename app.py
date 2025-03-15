from flask import Flask, request, jsonify
from flask_cors import CORS
import jiradata.data_service as JiraData
from jiradata.data_model import SprintSummary, JiraIssue

app = Flask(__name__)
CORS(app)

@app.route('/get-sprint-data', methods=['GET'])
def get_sprint_data():
    sprint_id = request.args.get('sprint_id')

    if not sprint_id:
        return jsonify({'error': 'Sprint Id is required'}), 400
    
    sprint_data = JiraData.getSprintInfo(sprint_id)

    if sprint_data:
        return jsonify(sprint_data)
    else:
        return jsonify({'error': 'Failed to fetch sprint data'}), 500
    

if __name__ == '__main__':
    app.run(debug=True)
