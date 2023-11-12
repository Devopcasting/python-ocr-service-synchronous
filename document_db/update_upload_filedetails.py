from document_db.connect import MongoDBConnection
from time import sleep

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
            result = []
            for document in documents:
                docs = {
                    "taskId": document['taskId'],
                    "status": document["status"],
                    "taskResult": document["taskResult"]
                }
                if self.__update_upload_filedetails(docs):
                    remove_query = {"taskId": document['taskId']}
                    collection.delete_one(remove_query)
            sleep(5)
    
    def __update_upload_filedetails(self, docinfo: dict) -> bool:
        filter = {"taskId": docinfo['taskId']}
        update = {"$set" : {
            "status": docinfo['status'],
            "taskResult": docinfo['taskResult']
        }}
        database = self.client["upload"]
        collection = database["fileDetails"]
        result = collection.update_one(filter, update)
        if result:
            return True
        else:
            return False