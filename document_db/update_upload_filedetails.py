from document_db.connect import MongoDBConnection
from time import sleep
import requests
import json

class UpdateUploadFileDetailsDB:
    def __init__(self) -> None:
        # Connect to Mongodb
        connection = MongoDBConnection()
        self.client = connection.get_connection()
    
    def query_status_ocrrworkspace(self):
        database = self.client["ocrrworkspace"]
        collection = database["ocrr"]
        query = {"status": {"$in": ["REJECTED", "REDACTED"]}}

        while True:
            documents = collection.find(query)
            for document in documents:
                client_id = document["clientId"]
                docs = {
                    "taskId": document['taskId'],
                    "status": document["status"],
                    "taskResult": document["taskResult"],
                    "clientId": document["clientId"],
                    "uploadDir": document["uploadDir"]
                }
                if self.__update_upload_filedetails(docs):
                    if self.__webhook_post_request(client_id, docs):
                        remove_query = {"taskId": document['taskId']}
                        collection.delete_one(remove_query)
            sleep(5)
    
    def __update_upload_filedetails(self, docinfo: dict) -> bool:
        filter_query = {"taskId": docinfo['taskId']}
        update = {"$set" : {
            "status": docinfo['status'],
            "taskResult": docinfo['taskResult']
        }}
        database = self.client["upload"]
        collection = database["fileDetails"]
        result = collection.update_one(filter_query, update)
        if result:
            return True
        return False
    
    def __webhook_post_request(self, clientid, payload: dict) -> bool:
        # Filter the clientId from upload:webhook
        filter_query = {"clientId": clientid}
        database = self.client["upload"]
        collection = database["webhook"]
        client_doc = collection.find_one(filter_query)

        WEBHOOK_URL = client_doc["url"]
        HEADER = {'Content-Type': 'application/json'}
        response = requests.post(WEBHOOK_URL+"/processstatus", data=json.dumps(payload), headers=HEADER)
        if response.status_code == 201 or response.status_code == 200 :
            return True
        return False
        