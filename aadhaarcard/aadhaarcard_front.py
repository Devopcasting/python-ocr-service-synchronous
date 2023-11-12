import pytesseract
import re
import os
from helpers.text_coordinates import TextCoordinates
from helpers.text_lang_coordinates import TextLangCoordinates
from document_db.update_ocrrworkspace import UpdateDocumentStatus


class AadhaarCardFrontInfo:
    def __init__(self, document_path: str, upload_path: str) -> None:
        self.document_path = document_path
        self.upload_path = upload_path
    
        # Get coordinates and OCR text output
        self.coordinates = TextCoordinates(self.document_path).generate_text_coordinates()
        self.coordinates_lang = TextLangCoordinates(self.document_path).generate_text_coordinates()

        self.text_eng = pytesseract.image_to_string(self.document_path)
        self.text_lang = pytesseract.image_to_string(self.document_path, lang="hin+eng")
                                                     
        # Set document original path
        document_name_list = os.path.basename(document_path).split('_')
        original_document_name = document_name_list[2]
        self.original_document_path = upload_path+"\\"+document_name_list[0]+"\\"+document_name_list[1]+"\\"+original_document_name

    
     # func: extract name in english and native language
    def __extract_name(self, index: int) -> list[list[int]]:
        """
            Extracts the name in English and Native language from the given text.
            Args:
                index: The index of the language to extract the name from. 1 for English, 2 for native language.
            Returns:
                A list of coordinates of the name in English or native language, or an empty list if the name cannot be found.
        """
        if index == 1:
            coords = self.coordinates
            text_lang = self.text_eng
        else:
            coords = self.coordinates_lang
            text_lang = self.text_lang
        
        name_lang_coords = self.__get_name_lang_coords(coords, text_lang, index)
        return name_lang_coords

    def __get_name_lang_coords(self, coords: list[tuple()], text_lang: str, index: int ) -> list[list[int]]:
        """
            Gets the coordinates of the name in English or native language.
            Args:
                coords: The coordinates of the text in English or native language.
                text_lang: The text in English or native language.
                index: The next index value of matching index.
            Returns:
                A list of coordinates of the name in English or native language, or an empty list if the name cannot be found.
        """
        name_lang_coords = []

        # Split the output text
        lines = [i for i in text_lang.splitlines() if len(i) != 0]

        # Find the matching word index
        matching_index = self.__find_matching_index(lines)
        if matching_index == 0:
            return name_lang_coords

        # Get coordinates of name in english or native language
        name_lang_list = lines[matching_index - index].split()
        if len(name_lang_list) > 1:
            name_lang_list = name_lang_list[:-1]

        for i,(x1, y1, x2, y2, text) in enumerate(coords):
            if text in name_lang_list:
                name_lang_coords.append([x1, y1, x2, y2])
            if len(name_lang_coords) == len(name_lang_list):
                break
            
        return name_lang_coords

    def __find_matching_index(self, text_lines: list) -> int:
        """
            Finds the matching index, which is the index of the line that contains the word "Year" or "DOB".
            Args
                text_lang: The text in English or native language.
            Returns:
                The index of the line that contains the word "Year" or "DOB", or None if the word is not found.
        """
        for i,text in enumerate(text_lines):
            if "Year" in text or "DOB" in text:
                return i
        return 0
    
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
    
    # func: collect Aadhaar card number
    def __extract_card_number(self) -> list:
        matching_index = 0
        pattern = r'[реж-реп]+'
        aadhaar_num_cords = []
        result = []
        # Get the matching text index
        for i,(x1,y1,x2,y2,text) in enumerate(self.coordinates):
            if text.lower() in ["male", "female"]:
                matching_index = i
                break
        if matching_index == 0:
            return result

        # Get the coordinates
        for i in range(matching_index, len(self.coordinates)):
            text = self.coordinates[i][4]
            if len(text) == 4 and text.isdigit() and not re.search(pattern, text):
                aadhaar_num_cords.append([self.coordinates[i][0], self.coordinates[i][1],
                                          self.coordinates[i][2], self.coordinates[i][3]])
            if len(aadhaar_num_cords) == 2:
                break
        if len(aadhaar_num_cords) < 2:
            return result
        
        # Get the final coordinates
        result = [aadhaar_num_cords[0][0], aadhaar_num_cords[0][1], aadhaar_num_cords[1][2], aadhaar_num_cords[1][3]]

        return result
        

    # func: collect Aadhaar card information
    def collect_aadhaarcard_front_info(self):
        aadhaar_card_info_list = []

        # Collect: name in native lang
        aadhaar_card_name_native_lang = self.__extract_name(2)
        if not aadhaar_card_name_native_lang:
            UpdateDocumentStatus(self.original_document_path, "REJECTED", "ERRAAD4").update_status()
            return aadhaar_card_info_list
        
        aadhaar_card_info_list.extend(aadhaar_card_name_native_lang)
                                          
        # Collect: Name in engish
        aadhaar_card_name_eng = self.__extract_name(1)
        if not aadhaar_card_name_eng:
            UpdateDocumentStatus(self.original_document_path, "REJECTED", "ERRAAD3").update_status()
            aadhaar_card_info_list = []
            return aadhaar_card_info_list
        
        aadhaar_card_info_list.extend(aadhaar_card_name_eng)

        # Collect: DOB
        aadhaar_card_dob = self.__extract_dob()
        if aadhaar_card_dob:
            aadhaar_card_info_list.append(aadhaar_card_dob)

        # Collect: Gender
        aadhaar_card_gender = self.__extract_gender()
        if aadhaar_card_gender:
            aadhaar_card_info_list.append(aadhaar_card_gender)
        else:
            UpdateDocumentStatus(self.original_document_path, "REJECTED", "ERRAAD2").update_status()
            aadhaar_card_info_list = []
            return aadhaar_card_info_list
        
        # Collect: Aadhaar card number
        aadhaar_card_num = self.__extract_card_number()
        if aadhaar_card_num:
            aadhaar_card_info_list.append(aadhaar_card_num)
        else:
            UpdateDocumentStatus(self.original_document_path, "REJECTED", "ERRAAD1").update_status()
            aadhaar_card_info_list = []
            return aadhaar_card_info_list
        
        return aadhaar_card_info_list