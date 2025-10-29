import asyncio
import os
import tempfile
import aiofiles
import subprocess
import time 
import json 
from pathlib import Path
# import aioboto3 
import boto3
from emb.db import pdb,dbindex,s3funcs
from emb.parsers.pdf.parse_pdf import read_pdf
from llama_index.core import Document as LlamaDocument  
from llama_index.core.schema import MetadataMode
# from llama_index.embeddings.huggingface_api  import HuggingFaceInferenceAPIEmbedding 
# from text_embeddings_inference_client import Client
from tei_client import HttpClient

from dotenv import load_dotenv

# Automatically load the .env file from the current directory or parent directories
load_dotenv()

# from src.db.pdb import Pgdb
# from src.emb.docz import DocEmbed

import logging
from logger.logging import configure_logging

log_ =  configure_logging()

# vector db
os.environ['PG_DATABASE'] = "embedding_db"
os.environ['PG_HOST'] = "192.168.3.164"
os.environ['PG_PORT'] = "5431"
os.environ['PG_USER'] = "dev_user"
os.environ['PG_PASSWORD'] = "dev_password"
# minio s3 storage
os.environ['LOCAL_S3_PROXY_SERVICE_URL'] = "http://192.168.3.164:9000"
os.environ['AWS_ACCESS_KEY_ID'] = "EJmZZD0aTifI0CIqb0K6"
os.environ['AWS_SECRET_ACCESS_KEY'] = "8HQervIK3M5JczQNQhNnHjand8Eo2Xhg2W5SF4wL"
# message q
os.environ['RABBIT_Q_STR'] = "amqp://guest:guest@192.168.3.164/"

# ref vector agvanced https://airbyte.com/data-engineering-resources/postgresql-as-a-vector-database 

db = pdb.Pgdb()

# xx = await db.adbconnpool()
# sdd = DocEmbed()

async def main():
    await db.adbconnpool()
    dbf = dbindex.FileIndex(db)    
    fileid = 5
    filename,category,s3_url,mimetype,bret = await dbf.get_file_attributes(fileid)
    # steps
    #  get doc info from db, create q entry,
    #  parse document as llama
    #  geberate embedding
    #  update q
    #  
    # get file for embedding by fileid

    # model_url = "http://192.168.3.26:8083"  # kali
    embedding_model_url = "http://192.168.3.164:8083"  # docker mitm
    # embed_model = HuggingFaceInferenceAPIEmbedding(
    #     model_name=embedding_model_url,
    #     token="HF_TOKEN",
    #     provider="auto",  # this will use the best provider available
    # )
    # client = Client(base_url=embedding_model_url)

    client = HttpClient(embedding_model_url)

    # mkey = "mydir/README-INSTRUCTIONS - Copy.pdf"
    minX = s3funcs.MinioS3()
    minX.connect()
    bytexs = minX.download_file_bytes("bucketa",s3_url)

    # Create a temporary file with YAML extension
    with tempfile.NamedTemporaryFile(delete=True, suffix=".pdf") as temp_file:
        temp_file.write(bytexs)
        temp_file_path = temp_file.name
        print(f"File stored temporarily at: {temp_file_path}")
        docs = read_pdf(temp_file_path)
        print(docs)
        # ------------------
        query = """INSERT INTO t_emb_1024 (text, metadata_, fileid, embedding) 
        VALUES ($1,$2,$3,$4) ON CONFLICT DO NOTHING RETURNING eid;"""
        bret = False
        result = -1
        async with db.connpool.acquire() as connection:        

            # upload documents to vector database without chunking 
            for document in docs:
                print("The LLM sees this: \n",document.get_content(metadata_mode=MetadataMode.LLM),)
                print("The Embedding model sees this: \n", document.get_content(metadata_mode=MetadataMode.EMBED),)            

                #embed_model = resolve_embed_model("local:BAAI/bge-large-en-v1.5")
                # embed_model = HuggingFaceInferenceAPIEmbedding(model_name="BAAI/bge-large-en-v1.5",)
                # do not embed if node is empty 
                if document.text_resource == None:
                    continue 
                emb_text = document.get_content(metadata_mode=MetadataMode.EMBED)
                result = await client.async_embed(emb_text,normalize=True)
                print(len(result[0]))
                metadata = document.metadata
                r = json.dumps(metadata)
                # test_embeds = embed_model.get_text_embedding(emb_text)

                # insert result in vector table 
                # fileid,bret = await dbf.insert_embedding(emb_text,metadata,"1",str(result[0]))            
                tr = connection.transaction()
                await tr.start()
                try:
                    # for query in sql:
                    result = await connection.fetchval(query,emb_text,r,str(fileid),str(result[0]))
                    
                except Exception as error:
                    await tr.rollback()
                    log_.error(f'ERROR: Unable to execute:  {error}')              
                    # raise
                else:
                    await tr.commit()
                    bret = True        






    # yield
    # await sdd.adbclose()
    await db.adbclosepool()

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    results = loop.run_until_complete(main())
    loop.close()
    print(results)    
    print('end')    
