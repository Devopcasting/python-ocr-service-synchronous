import os
import re
import pytesseract
from helpers.text_coordinates import TextCoordinates
from helpers.text_lang_coordinates import TextLangCoordinates
from document_db.update_ocrrworkspace import UpdateDocumentStatus
from ocrr_log_mgmt.ocrr_log import OCRREngineLogging

class EAadhaarCardInfo:
    def __init__(self, document_path: str, upload_path: str) -> None:
        self.document_path = document_path
        self.upload_path = upload_path
    
        # Configure logger
        log_config = OCRREngineLogging()
        self.logger = log_config.configure_logger()

        # Get coordinates and OCR text output
        self.coordinates = TextCoordinates(self.document_path).generate_text_coordinates()
        self.coordinates_lang = TextLangCoordinates(self.document_path).generate_text_coordinates()

        self.text_eng = pytesseract.image_to_string(self.document_path)
        self.text_lang = pytesseract.image_to_string(self.document_path, lang="hin+eng")
                                                     
        # Set document original path
        document_name_list = os.path.basename(document_path).split('+')
        original_document_name = document_name_list[2]
        self.original_document_path = upload_path+"\\"+document_name_list[0]+"\\"+document_name_list[1]+"\\"+original_document_name

     # func: top side native language name
    def __top_native_eng_lang_name(self, index: int) -> list:

        result = []

        # clean text list
        clean_text = [i for i in self.text_lang.split("\n") if len(i) != 0]
        # get matching text below
        matching_text = self.__below_matching_text(clean_text, index)
        if not matching_text:
            return result
        
        result = self.__get_top_native_name_coords(matching_text, self.coordinates_lang)
        return result
    
    # func: find text below matching text
    def __below_matching_text(self, clean_text: list, index: int) -> list:
        # find text below matching text
        matching_text = []
        for i,text in enumerate(clean_text):
            if "To" in text:
                matching_text = clean_text[i + index].split()
                break
        return matching_text
    
    # func: get top native name coordinates
    def __get_top_native_name_coords(self, matching_text: list, coords) -> list:
        result = []
         
        if len(matching_text) > 1:
            matching_text = matching_text[:-1]

        for i,(x1, y1, x2, y2, text) in enumerate(coords):
            if text in matching_text:
                result.append([x1, y1, x2, y2])
            if len(matching_text) == len(result):
                break
        return result
        
    # func: extract dob
    def __extract_dob(self) -> list:
        dob_coordinates = []
        result = []
        matching_index = 0

        # Get the index of Male or Female
        for i ,(x1,y1,x2,y2,text) in enumerate(self.coordinates):
            if text.lower() in ["male", "female"]:
                matching_index = i
                break
        if matching_index == 0:
            return result
        
        # Reverse loop from Male/Female index until DOB comes
        for i in range(matching_index, -1, -1):
            if re.match(r'^\d{2}/\d{2}/\d{4}$', self.coordinates[i][4]) or re.match(r'^\d{4}$', self.coordinates[i][4]):
                dob_coordinates = [self.coordinates[i][0], self.coordinates[i][1], self.coordinates[i][2], self.coordinates[i][3]]
                break
        if not dob_coordinates:
            return result
      
        # Get first 6 chars
        width = dob_coordinates[2] - dob_coordinates[0]
        result = [dob_coordinates[0], dob_coordinates[1], dob_coordinates[0] + int(0.54 * width), dob_coordinates[3]]
        return result
    
    # func: extract gender
    def __extract_gender(self) -> list:
        gender_coordinates = []
        result = []
        matching_index = 0

        # Get the index of Male or Female
        for i ,(x1,y1,x2,y2,text) in enumerate(self.coordinates):
            if text.lower() in ["male", "female"]:
                matching_index = i
                break
        if matching_index == 0:
            return result
        
        # Reverse loop from Male/Female index until DOB comes
        for i in range(matching_index, -1, -1):
            if re.match(r'^\d{2}/\d{2}/\d{4}$', self.coordinates[i][4]) or re.match(r'^\d{4}$', self.coordinates[i][4]):
                break
            else:
                gender_coordinates.append([self.coordinates[i][0], self.coordinates[i][1], 
                                           self.coordinates[i][2], self.coordinates[i][3]])
        # Prepare final coordinates
        result = [gender_coordinates[-1][0], gender_coordinates[-1][1], gender_coordinates[0][2], gender_coordinates[0][3]]
        return result
    
    # func: collect aadhaar card number
    def __extract_eaadharcard_number(self, matching_text: str) -> list:
        text = [ i for i in self.text_eng.split("\n") if len(i) != 0 ]
        result = []
        eaadhaar_num = None
        eaadhaar_coords = []

        for i, line in enumerate(text):
            if matching_text in line:
                eaadhaar_num = text[i + 1].split()
                eaadhaar_num = [ i for i in eaadhaar_num if i.isdigit() and len(i) == 4]
                break
        if eaadhaar_num is None or len(eaadhaar_num) < 3:
            return result
        
        # get the coordinates
        for i,(x1, y1, x2, y2, t) in enumerate(self.coordinates):
            if t in eaadhaar_num:
                eaadhaar_coords.append([x1, y1, x2, y2])
        if len(eaadhaar_coords) != 6:
            return result
        
        # combine coordinates
        result.append([eaadhaar_coords[0][0], eaadhaar_coords[0][1], eaadhaar_coords[1][2], eaadhaar_coords[1][3]])
        result.append([eaadhaar_coords[3][0], eaadhaar_coords[3][1], eaadhaar_coords[4][2], eaadhaar_coords[4][3]])

        return result
    
    # func: collect E-Aadhaar card information
    def collect_eaadhaarcard_info(self):
        eaadhaarcard_info_list = []

        # Collect: Top side name in native language
        top_side_native_lang_name = self.__top_native_eng_lang_name(1)
        if not top_side_native_lang_name:
            self.logger.error(f"| Document Rejected with error ERREAAD4: {self.original_document_path}")
            UpdateDocumentStatus(self.original_document_path, "REJECTED", "ERREAAD4").update_status()
            return eaadhaarcard_info_list
        eaadhaarcard_info_list.extend(top_side_native_lang_name)

        # Collect: Top side name in english language
        top_side_eng_lang_name = self.__top_native_eng_lang_name(2)
        if not top_side_eng_lang_name:
            self.logger.error(f"| Document Rejected with error ERREAAD3: {self.original_document_path}")
            UpdateDocumentStatus(self.original_document_path, "REJECTED", "ERREAAD3").update_status()
            return eaadhaarcard_info_list
        eaadhaarcard_info_list.extend(top_side_eng_lang_name)
        
        # Collect: DOB
        aadhaar_card_dob = self.__extract_dob()
        if aadhaar_card_dob:
            eaadhaarcard_info_list.append(aadhaar_card_dob)

        # Collect: E-Aadhaar card Gender
        e_aadhaar_card_gender = self.__extract_gender()
        if not e_aadhaar_card_gender:
            self.logger.error(f"| Document Rejected with error ERREAAD2: {self.original_document_path}")
            UpdateDocumentStatus(self.original_document_path, "REJECTED", "ERREAAD2").update_status()
            eaadhaarcard_info_list = []
            return eaadhaarcard_info_list
        eaadhaarcard_info_list.append(e_aadhaar_card_gender)

        # Collect: E-Aadhaar card number
        e_aadhaar_card_num = self.__extract_eaadharcard_number("Aadhaar")
        if not e_aadhaar_card_num:
            self.logger.error(f"| Document Rejected with error ERREAAD1: {self.original_document_path}")
            UpdateDocumentStatus(self.original_document_path, "REJECTED", "ERREAAD1").update_status()
            eaadhaarcard_info_list = []
            return eaadhaarcard_info_list
        eaadhaarcard_info_list.extend(e_aadhaar_card_num)

        return eaadhaarcard_info_list