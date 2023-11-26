import os
import xml.etree.ElementTree as ET

class WriteXML:
    def __init__(self, redacted_path: str, original_document_name: str, ocr_obj_info: list) -> None:
        self.xml_path = redacted_path
        self.xml_file_name = original_document_name
        self.content = ocr_obj_info
    
    def writexml(self) -> bool:
        # Set XML file path
        xml_file_path = os.path.join(self.xml_path, self.xml_file_name.split('.')[0]+'.xml')
        if os.path.exists(xml_file_path):
            os.remove(xml_file_path)

        # Prepare data
        data = []
        count_index = 1
        for i in self.content:
            x1, y1, x2, y2 = i
            data.append(f'0,0,0,,,,0,0,0,0,0,0,,vv,cvadmin,vv,0,1,0,{count_index},{x1},{y1},{x2},{y2},0,0,')
            x1, y1, x2, y2 = [0, 0, 0, 0]
            count_index = count_index + 1
        # Create the root element    
        root = ET.Element("DataBase")

        # Add count element
        count = ET.SubElement(root, "Count")
        count.text = f'{len(data)}'

        # Create the DatabaseRedactions element
        database_redactions = ET.SubElement(root, "DatabaseRedactions")

        # Create DatabaseRedaction elements in a loop
        for i, item in enumerate(data, start=1):
            database_redaction = ET.SubElement(database_redactions, "DatabaseRedaction", ID=str(i))
            database_redaction.text = item
        
        # Create an ElementTree object
        tree = ET.ElementTree(root)

        # Write the XML to a file or print it
        tree.write(xml_file_path , encoding="utf-8", xml_declaration=True)

        return True
