from pathlib import Path 
from llama_index.core import SimpleDirectoryReader

from llama_index.readers.file import (
    # DocxReader,
    # HWPReader,
    # PDFReader,
    # EpubReader,
    # FlatReader,
    # HTMLTagReader,
    # ImageCaptionReader,
    # ImageReader,
    # ImageVisionLLMReader,
    # IPYNBReader,
    # MarkdownReader,
    MboxReader,
    PptxReader,
    # PandasCSVReader,
    # VideoAudioReader,
    # UnstructuredReader,
    # PyMuPDFReader,
    # ImageTabularChartReader,
    # XMLReader,
    # PagedCSVReader,
    # CSVReader,
    # RTFReader,
)
from llama_index.core import Document #as LlamaDocument  


# ref: https://pypi.org/project/langchain-excel-loader

def read_ppt(file_path,file_folder):
    # Pptx Reader example
    # Basic usage - extracts text, tables, charts, and speaker notes
    parser = PptxReader()

    # Advanced usage - control parsing behavior
    parser = PptxReader(
        extract_images=False,  # Enable image captioning
        context_consolidation_with_llm=False,  # Use LLM for content synthesis
        num_workers=1,  # Parallel processing
        batch_size=10,  # Slides processed per worker batch
        raise_on_error=True,  # Raise value error if file_parsing is not successful
    )
    file_extractor = {".ppt": parser}
    docs = SimpleDirectoryReader(file_folder, file_extractor=file_extractor).load_data()

    # llama_parse_documents = LlamaParse(result_type="markdown").load_data("./data/presentation.pptx")

    # loader = StructuredExcelLoader(file_path=file_path,                
    #             # headers = None
    #             # password = None,
    #             # mode = "page",
    #             # pages_delimiter = "\n\f",
    #             # extract_images = True,
    #             # images_parser = TesseractBlobParser(),
    #             # extract_tables = "markdown",
    #             # extract_tables_settings = None,
    #             )
    # docs = loader.load()
    # llamaDocs = [LlamaDocument.from_langchain_format(doc=document) for document in docs]    
    return docs

if __name__ == "__main__":
    # file_path = "/mnt/soft/contcode/pandoc/test_data/pdf/P4 AMENDED APPROVAL.pdf" #Path(r"S:\temp_pandoc\pdf\P4 AMENDED APPROVAL.pdf")
    file_path = "/mnt/soft/contcode/pandoc/test_data/pptx/dhis2.pptx"
    docs = read_ppt(file_path,"/mnt/soft/contcode/pandoc/test_data/ppt/")

    print(docs)

    print("end")
