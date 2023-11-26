from document_db.connect import MongoDBConnection
from time import sleep

class FilterInProgress:
    def __init__(self, upload_path: str, inprogress_queue: object) -> None:
        # Set paths
        self.upload_path = upload_path
        self.inprogress_queue = inprogress_queue
    
        # Connect to Mongodb
        connection = MongoDBConnection()
        client = connection.get_connection()
        # Select upload db
        db_upload = client["upload"]
        self.collection_upload = db_upload['fileDetails']

        # Select ocrrworkspace db
        db_ocrrworkspace = client['ocrrworkspace']
        self.collection_ocrrworkspace = db_ocrrworkspace['ocrr']

    def query_inprogress_status(self):
        """
            Query database with filter status:IN_PROGRESS
            Put the document path in queue
        """
        query = {"status": "IN_PROGRESS"}
        while True:
            documents = self.collection_upload.find(query)
            document_sub_path = ""
            document_path = ""
            document_path_list = []
            for document in documents:
                document_path_list = document['uploadDir'].split('/')
                for i in range(len(document_path_list)):
                    if len(document_path_list[i]) !=0:    
                        document_sub_path += '\\'+document_path_list[i]

                document_path = self.upload_path+document_sub_path
                print(document_path)
                status = document['status']
                clientid = document['clientId']
                taskid = document['taskId']
                uploaddir = document['uploadDir']
                # call insert_document_info
                self.__insert_document_info(taskid, document_path, status, clientid, uploaddir)
                document_sub_path = ""
                document_path = ""
                document_path_list = []
            sleep(5)
    
    # Insert new IN_PROGRESS document information in ocrrworkspace-ocrr.
    # Put the document path in a queue
    def __insert_document_info(self, taskid, document_path, status, clientid, uploaddir):
        # Call query_taskid
        if self.__query_taskid(taskid):
            document = {
                "taskId": taskid,
                "path": document_path,
                "status": status,
                "clientId": clientid,
                "taskResult": "",
                "uploadDir": uploaddir
            }
            self.collection_ocrrworkspace.insert_one(document)
            self.inprogress_queue.put(document_path)
            # Update the IN_PROGRESS status
            self.__update_in_progress_status(taskid)

    # Check if the taskId already available in ocrrworkspace-ocrr
    def __query_taskid(self, taskid) -> bool:
        query = {"taskId": taskid}
        result = self.collection_ocrrworkspace.find_one(query)
        if not result:
            return True
        return False

    # Update the status from IN_PROGRESS to  IN_QUEUE
    def __update_in_progress_status(self, taskid):
        query = {"taskId": taskid}
        update = {"$set":{"status": "IN_QUEUE"}}
        self.collection_upload.update_one(query, update)