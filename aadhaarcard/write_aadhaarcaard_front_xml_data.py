from aadhaarcard.aadhaarcard_front import AadhaarCardFrontInfo
from document_db.update_ocrrworkspace import UpdateDocumentStatus
from ocrr_log_mgmt.ocrr_log import OCRREngineLogging
from helpers.xmldata import WriteXML
import os
import shutil
from pathlib import Path
from rejected_redacted.redacted_rejected_document import RedactRejectedDocument


class WriteAadhaarCardFrontXMLData:
    def __init__(self, get_doc_dict: dict, document_path: str, upload_path: str) -> None:
        self.document_path = document_path
        self.upload_path = upload_path
        self.get_doc_dict = get_doc_dict

        # Configure logger
        log_config = OCRREngineLogging()
        self.logger = log_config.configure_logger()

    
    def writexmldata(self) -> bool:
        # Perform OCR
        ocrr = AadhaarCardFrontInfo(self.document_path, self.upload_path)
        ocrr_info = ocrr.collect_aadhaarcard_front_info()

        if ocrr_info:
            write_xml = WriteXML(self.get_doc_dict["document_redacted_path"], self.get_doc_dict["original_document_name"], ocrr_info )
            if write_xml.writexml():
                self.__redacted()
                return True
            else:
                self.__rejected("ERRAAD6")
                return False
        else:
            self.__rejected("ERRAAD5")
            return False
    
    def __redacted(self):
        if os.path.exists(self.document_path):
            # Move the original document to Redacted folder
            shutil.move(self.get_doc_dict["original_document_path"], os.path.join(self.get_doc_dict["document_redacted_path"], self.get_doc_dict["original_document_name"]))
            # Delete document from workspace
            path = Path(self.document_path)
            path.unlink()
            self.logger.info(f"| Document Redacted successfully: {self.get_doc_dict["original_document_path"]}")
            # Update status of ocrrworkspace-ocrr
            UpdateDocumentStatus(self.get_doc_dict["original_document_path"], "REDACTED", "Uploaded Successfully").update_status()
    
    def __rejected(self, error_code: str):
        if os.path.exists(self.document_path):
            # Get 75% redacted coordinates of the image
            redact_rejected_doc = RedactRejectedDocument(self.get_doc_dict["original_document_path"])
            coordinates_list = redact_rejected_doc.rejected()
            write_xml = WriteXML(self.get_doc_dict["document_rejected_path"], self.get_doc_dict["original_document_name"], coordinates_list)
            write_xml.writexml()
            
            # Move the original document to Rejected folder
            shutil.move(self.get_doc_dict["original_document_path"], os.path.join(self.get_doc_dict["document_rejected_path"], self.get_doc_dict["original_document_name"]))
            path = Path(self.document_path)
            path.unlink()
            self.logger.error(f"| Document Rejected with error {error_code}: {self.get_doc_dict["original_document_path"]}")
            # Update status of ocrrworkspace-ocrr
            UpdateDocumentStatus(self.get_doc_dict["original_document_path"], "REJECTED", error_code).update_status()

