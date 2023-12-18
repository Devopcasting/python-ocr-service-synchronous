import cv2
import shutil
import os
from time import sleep
from ocrr_log_mgmt.ocrr_log import OCRREngineLogging

class ProcessDocuments:
    def __init__(self, inprogress_queue: object, workspace_path: str, processed_doc_queue: object) -> None:
        # Set paths
        self.workspace_path = workspace_path
        
        # Set Queues
        self.inprogress_queue = inprogress_queue
        self.processed_doc_queue = processed_doc_queue

        # Configure logger
        log_config = OCRREngineLogging()
        self.logger = log_config.configure_logger()

        # Document processing cv2 values
        self.sigma_x = 1
        self.sigma_y = 1
        self.sig_alpha = 1.5
        self.sig_beta = -0.2
        self.gamma = 0

    def process_doc(self):
        while True:
            document_path = self.inprogress_queue.get()
            if document_path is not None:
                # Copy the document to workspace path
                document_name = os.path.basename(document_path)
                shutil.copy(document_path, os.path.join(self.workspace_path, document_name))

                # Create workspace path for document
                workspace_path_doc = os.path.join(os.path.join(self.workspace_path, document_name))

                # Check for document Gray or Coloured
                if self.__isgray(workspace_path_doc):
                    doc_rename = self.__rename_doc(document_path)
                    shutil.move(workspace_path_doc, os.path.join(self.workspace_path, doc_rename))
                    self.processed_doc_queue.put(os.path.join(self.workspace_path, doc_rename))
                    self.logger.info(f"| Document Processed: {workspace_path_doc}")
                else:
                    doc_rename = self.__rename_doc(document_path)
                    if self.__processed_coloured_docs(workspace_path_doc, doc_rename):
                        self.logger.info(f"| Document Processed: {workspace_path_doc}")
                    else:
                        self.logger.error(f"| Error processing docuemnt: {workspace_path_doc}")
            sleep(5)

    def __processed_coloured_docs(self, workspace_path_doc, doc_rename) -> bool:
        document = cv2.imread(workspace_path_doc)
        try:
            denoise_document = cv2.fastNlMeansDenoisingColored(document, None,  10, 10, 7, 21)
            gray_document = cv2.cvtColor(denoise_document, cv2.COLOR_BGR2GRAY)
            gaussian_blur_document = cv2.GaussianBlur(gray_document, (5,5), sigmaX=self.sigma_x, sigmaY=self.sigma_y )
            sharpened_image = cv2.addWeighted(gray_document, self.sig_alpha, gaussian_blur_document, self.sig_beta, self.gamma)
            sharpened_image_gray = cv2.cvtColor(sharpened_image, cv2.COLOR_GRAY2BGR)
            cv2.imwrite(os.path.join(self.workspace_path, doc_rename), sharpened_image_gray)
            self.processed_doc_queue.put(os.path.join(self.workspace_path, doc_rename))
            os.remove(workspace_path_doc)
            return True
        except Exception:
            return False

    def __isgray(self, workspace_path_doc):
        document = cv2.imread(workspace_path_doc)
        if len(document.shape) < 3: return True
        if document.shape[2]  == 1: return True
        b,g,r = document[:,:,0], document[:,:,1], document[:,:,2]
        if (b==g).all() and (b==r).all(): return True
        return False

    def __rename_doc(self, document_path) -> str:
        renamed_doc_list = document_path.split("\\")
        renamed_doc = renamed_doc_list[-3]+"+"+renamed_doc_list[-2]+"+"+renamed_doc_list[-1]
        return renamed_doc