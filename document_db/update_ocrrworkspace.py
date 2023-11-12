from document_db.connect import MongoDBConnection

class UpdateDocumentStatus:
    def __init__(self, original_document_path: str, status: str, taskresult: str) -> None:
        # Create DB connection
        connection = MongoDBConnection()
        client = connection.get_connection()
        database = client["ocrrworkspace"]
        self.collection = database["ocrr"]

        # Set values
        self.original_document_path = original_document_path
        self.status = status
        self.taskresult = taskresult
    
    def update_status(self):
        query = {"path": self.original_document_path}
        update = {"$set" : {
            "status": self.status,
            "taskResult": self.taskresult
        }}

        self.collection.update_one(query, update)