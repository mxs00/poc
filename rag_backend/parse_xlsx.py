from pathlib import Path 
from langchain_excel_loader import StructuredExcelLoader
from llama_index.core import Document as LlamaDocument  


# ref: https://pypi.org/project/langchain-excel-loader

def read_xls(file_path):
    loader = StructuredExcelLoader(file_path=file_path,                
                # headers = None
                # password = None,
                # mode = "page",
                # pages_delimiter = "\n\f",
                # extract_images = True,
                # images_parser = TesseractBlobParser(),
                # extract_tables = "markdown",
                # extract_tables_settings = None,
                )
    docs = loader.load()
    llamaDocs = [LlamaDocument.from_langchain_format(doc=document) for document in docs]    
    return llamaDocs

if __name__ == "__main__":
    # file_path = "/mnt/soft/contcode/pandoc/test_data/pdf/P4 AMENDED APPROVAL.pdf" #Path(r"S:\temp_pandoc\pdf\P4 AMENDED APPROVAL.pdf")
    file_path = "/mnt/soft/contcode/pandoc/app/parsers/xls/website schema.xlsx"
    docs = read_xls(file_path=file_path)

    print(docs)

    print("end")
