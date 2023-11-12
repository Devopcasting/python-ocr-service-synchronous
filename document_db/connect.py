import pymongo

class MongoDBConnection:
    def __init__(self):
        self.connection_string = "mongodb://localhost:27017"
        self.database_name = "ocrrworkspace"
        self.collection_name = "ocrr"

    def get_connection(self):
        client = pymongo.MongoClient(self.connection_string)
        return client
    
    # Create Database and Collection
    def create_database_and_collection(self):
        client = self.get_connection()

        # Create database if it doesn't exists
        db_names = client.list_database_names()
        if self.database_name not in db_names:
            database = client[self.database_name]
            # Create collection if it doesn't exists
            if self.collection_name not in database.list_collection_names():
                database.create_collection(self.collection_name)
