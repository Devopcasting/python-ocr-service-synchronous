import pytesseract
import re
import os
from helpers.text_coordinates import TextCoordinates
from document_db.update_ocrrworkspace import UpdateDocumentStatus
from ocrr_log_mgmt.ocrr_log import OCRREngineLogging

class PassportDocumentInfo:
    def __init__(self, document_path, upload_path) -> None:
        # Configure logger
        log_config = OCRREngineLogging()
        self.logger = log_config.configure_logger()

        # Set document original path
        document_name_list = os.path.basename(document_path).split('+')
        original_document_name = document_name_list[2]
        self.original_document_path = upload_path+"\\"+document_name_list[0]+"\\"+document_name_list[1]+"\\"+original_document_name

        # Get the coordinates of all the extracted text
        self.coordinates = TextCoordinates(document_path, doc_type="passport").generate_text_coordinates()
        # Get the texts from document
        self.text = pytesseract.image_to_string(document_path)
    
    def __extract_passport_number(self) -> list:
        matching_line_index_top = None
        matching_line_index_bottom = None
        matching_passport_text = None
        matching_text = "passport"
        matching_passport_number_coords_top = []
        matching_passport_number_coords_bottom = []
        result = []

        # find matching text coordinates
        for i,(x1, y1, x2, y2, text) in enumerate(self.coordinates):
            if matching_text in text.lower():
                matching_line_index_top = i
                break
        if matching_line_index_top is None:
            return result
       
        # find the top Passport coordinates
        for i in range(matching_line_index_top, len(self.coordinates)):
            text = self.coordinates[i][4]
            if len(text) == 8 and text.isupper() and text.isalnum():
                matching_passport_number_coords_top = [self.coordinates[i][0], self.coordinates[i][1],
                                         self.coordinates[i][2], self.coordinates[i][3]]
                matching_line_index_bottom = i
                matching_passport_text = text
                break

        if matching_line_index_bottom is None:
            return result
        
        # find the top Passport coordinates
        for i in range(matching_line_index_bottom + 1, len(self.coordinates)):
            text = self.coordinates[i][4]
            if matching_passport_text in text:
                matching_passport_number_coords_bottom = [self.coordinates[i][0], self.coordinates[i][1],
                                         self.coordinates[i][2], self.coordinates[i][3]]
                break
        if not matching_passport_number_coords_bottom:
            return result
       
        result.append(matching_passport_number_coords_top)
        result.append(matching_passport_number_coords_bottom)
        return result



    # func: collect pancard information
    def collect_passport_info(self) -> list:
        passport_doc_info_list = []

        # Collect: Passport Number
        passport_number = self.__extract_passport_number()
        if not passport_number:
            self.logger.error(f"| Document Rejected with error ERRPASS1: {self.original_document_path}")
            UpdateDocumentStatus(self.original_document_path, "REJECTED", "ERRPASS1").update_status()
            return passport_doc_info_list
        passport_doc_info_list.extend(passport_number)
        return passport_doc_info_list

