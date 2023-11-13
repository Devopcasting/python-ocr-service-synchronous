import configparser
import threading
import multiprocessing as mp
from document_db.connect import MongoDBConnection
from document_db.filter_in_progress import FilterInProgress
from document_db.update_upload_filedetails import UpdateUploadFileDetailsDB
from document_processing.doc_processing import ProcessDocuments
from write_xml_data.xml_data import WriteXMLDatas

class OCRREngine:
    def __init__(self) -> None:
        # Create OCRR Workspace DB if not present
        document_db_client = MongoDBConnection()
        document_db_client.create_database_and_collection()

        # Set queues
        self.inprogress_queue = mp.Queue()
        self.processed_doc_queue = mp.Queue()
    
    def start_ocrr_engine(self):
        """
            Thread:
            Query filter database for status:IN_PROGRESS.
            Put the path in queue
        """
        query_inprogress_obj = FilterInProgress(upload_path, self.inprogress_queue)
        query_inprogress_thread = threading.Thread(target=query_inprogress_obj.query_inprogress_status)

        """
            Multi-Processing:
            Get the document path from inprogress_queue
            Process and move the document to workspace
            Put the workspace document path in processed_doc_queue
        """
        process_document_obj = ProcessDocuments(self.inprogress_queue, workspace_path, self.processed_doc_queue)
        process_document_process = mp.Process(target=process_document_obj.process_doc)

        """
            Multi-Processing
            - Get the Processed document paths
            - Identify the document
                - Pancard
                - Aadhaar Card
                - E-Aadhaar Card
                - Passport
            - Perform OCR and write the Coordinates XML data file
        """
        write_xml_data_obj = WriteXMLDatas(self.processed_doc_queue, upload_path)
        write_xml_data_process = mp.Process(target=write_xml_data_obj.xml)

        """
            Thread:
            Filter the 'REDACTED', 'RJECTED' from ocrrworkspace-ocrr
            Update the 'status' and 'taskResult' of upload.fileDetails
        """
        update_upload_db_obj = UpdateUploadFileDetailsDB()
        update_upload_db_thread = threading.Thread(target=update_upload_db_obj.query_status_ocrrworkspace)

        # Start Threads and Multi-Processes
        query_inprogress_thread.start()
        process_document_process.start()
        write_xml_data_process.start()
        update_upload_db_thread.start()

if __name__ == '__main__':
    # Read config.ini
    config = configparser.ConfigParser(allow_no_value=True)
    config.read(r'C:\Users\pokhriyal\Desktop\Minimal\config.ini')
    # Set Path vars
    upload_path = config['Paths']['upload']
    workspace_path = config['Paths']['workspace']

    obj = OCRREngine()
    obj.start_ocrr_engine()