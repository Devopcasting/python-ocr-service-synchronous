from time import sleep
import os
import shutil
from pathlib import Path
from document_identification.identify_documents import DocumentIdentification
from ocrr_log_mgmt.ocrr_log import OCRREngineLogging
from pancard.write_xml_data import WritePanCardXMLData
from aadhaarcard.write_eaadhaarcard_xml_data import WriteEAadhaarCardXMLData
from aadhaarcard.write_aadhaarcaard_front_xml_data import WriteAadhaarCardFrontXMLData
from document_db.update_ocrrworkspace import UpdateDocumentStatus


class WriteXMLDatas:
    def __init__(self,  processed_doc_queue: object, upload_path: str) -> None:
        # Set paths
        self.upload_path = upload_path
        # Set Queues
        self.processed_doc_queue = processed_doc_queue

        # Configure logger
        log_config = OCRREngineLogging()
        self.logger = log_config.configure_logger()

    def xml(self):
        while True:
            document_path = self.processed_doc_queue.get()
            if document_path is not None:
                get_doc_dict = self.__set_orginal_doc_dict(document_path)
                document_obj = DocumentIdentification(document_path)
                # Identify document: Pancard
                if document_obj.identify_pancard():
                    self.__process_pancard(get_doc_dict, document_path) 
                # Identify document: Aadhaar card
                elif document_obj.identify_aadhaarcard():
                    if document_obj.identify_eaadhaarcard():
                          self.__process_eaadhaarcard(get_doc_dict, document_path)
                    elif document_obj.identify_aadhaarcard_front():
                        self.__process_aadhaarcard_front(get_doc_dict, document_path)
                    else:
                        self.__rejected(get_doc_dict, document_path, "ERRAAD7")
                else:
                    self.__rejected(get_doc_dict, document_path, "ERRDOC1")
            sleep(10)
    
    def __process_pancard(self, get_doc_dict,  document_path):
        # Perform OCR and Write XML
        if WritePanCardXMLData(get_doc_dict, document_path, self.upload_path).writexmldata():
            self.logger.info(f"| OCR successful: {document_path}")
        else:
            self.logger.error(f"| Error performing OCR: {document_path}")

    def __process_eaadhaarcard(self, get_doc_dict, document_path):
        # Perform OCR and Write XML
        if WriteEAadhaarCardXMLData(get_doc_dict, document_path, self.upload_path).writexmldata():
            self.logger.info(f"| OCR successful: {document_path}")
        else:
            self.logger.error(f"| Error performing OCR: {document_path}")

    def __process_aadhaarcard_front(self, get_doc_dict, document_path):
        # Perform OCR and Write XM
        if WriteAadhaarCardFrontXMLData(get_doc_dict, document_path, self.upload_path).writexmldata():
            self.logger.info(f"| OCR successful: {document_path}")
        else:
            self.logger.error(f"| Error performing OCR: {document_path}")

    def __set_orginal_doc_dict(self, document_path) -> dict:
        document_name_list = os.path.basename(document_path).split('_')
        original_document_name = document_name_list[2]
        original_document_path = self.upload_path+"\\"+document_name_list[0]+"\\"+document_name_list[1]+"\\"+original_document_name
        document_redacted_path = self.upload_path+"\\"+document_name_list[0]+"\\"+document_name_list[1]+"\\Redacted"
        document_rejected_path = self.upload_path+"\\"+document_name_list[0]+"\\"+document_name_list[1]+"\\Rejected"
        document_dict = {
            "document_redacted_path": document_redacted_path,
            "document_rejected_path": document_rejected_path,
            "original_document_name": original_document_name,
            "original_document_path": original_document_path
        }
        return document_dict

    def __rejected(self, get_doc_dict: dict, document_path: str, error_code: str):
        # Move the original document to Rejected folder
        shutil.move(get_doc_dict["original_document_path"], os.path.join(get_doc_dict["document_rejected_path"], get_doc_dict["original_document_name"]))
        path = Path(document_path)
        path.unlink()
        self.logger.error(f"| Document Rejected with error {error_code}: {document_path}")
        # Update status of ocrrworkspace-ocrr
        UpdateDocumentStatus(get_doc_dict["original_document_path"], "REJECTED", error_code).update_status()
