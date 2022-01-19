# from os import getenv
# import pymssql
# import datetime
# import configparser
# import os

# import jiradata.data_service as data

# # prepare database info
# config = configparser.ConfigParser()
# configFilePath = os.path.join(os.path.dirname(__file__) + r'/../app.ini')
# config.read(configFilePath, encoding='utf-8')

# DB_HOST = config.get('Database', 'HOST')
# DB_USERNAME = config.get('Database', 'USERNAME')
# DB_PASSWORD = config.get('Database', 'PASSWORD')

# # capture data snapshot for sprint or board
# def captureDataSnapshot(type, id):
#     info = {}
#     issues = []
#     server_type_id = 0

#     conn = pymssql.connect(host=DB_HOST,
#                            user=DB_USERNAME,
#                            password=DB_PASSWORD,
#                            database='JiraStatCollector',
#                            charset='iso-8859-1')
#     cursor = conn.cursor()

#     if type == 'sprint':
#         info = data.getSprintInfo(id)
#         issues = data.getSprintIssuesViaRequest(id)
#         server_type_id = 1
#     elif type == 'board':
#         info = data.getBoardInfo(id)
#         issues = data.getBoardIssues(id)
#         server_type_id = 2

#     cursor.executemany(
#         "INSERT INTO [DataSnapshot] ('ServerType', 'ServeId', 'SnapshotTime') VALUES (%d, %d, %s)",
#         [(server_type_id, id,
#           datetime.date.today().strftime('%Y-%m-%d %H:%M:%S.%Z'))])

#     conn.commit()

#     conn.close()