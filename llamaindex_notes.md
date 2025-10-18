
source llindex/bin/activate

uv pip install openai
uv pip install llama-index
uv pip install llama-index-vector-stores-postgres
uv pip install llama-index-readers-file
uv pip install llama-index-embeddings-huggingface
uv pip install 'markitdown[all]'
uv pip install llama-index-embeddings-huggingface
uv pip install llama-index-vector-stores-postgres

#web services
fastapi
uvicorn
python-multipart
python-dotenv

#async io
#litserve
aiofiles
boto3

# document parsers 
pymupdf


# opencv-python==4.8.0.74
# opencv-contrib-python
# opencv-python-headless

llama-index-core 
langchain-community
# unstructured[all-docs]

langchain-excel-loader
openpyxl

extract_msg
llama-index-readers-file
llama-index-llms-openai
python-pptx


raw json
'''
{
    "inputs": "page_label: 2\nfile_path: D:\\temp\\embedding\\pdf\\abc.pdf\n\n2  \n \n \n \nContents \n1: Artificial Intelligence & Machine Learning Services ................................................................................ 3 \n2: Expertise in AI Models & Frameworks .................................................................................................... 4 \n3: Expertise in Foundation Technologies .................................................................................................... 5 \n4: AI Use Cases ............................................................................................................................................ 6 \n4.1 Use Case: Preserving Intellectual Property by Hosting Large language models (LLMs) on premise .. 6 \n5: Development Environment ..................................................................................................................... 9"
}
'''
