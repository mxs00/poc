import sys
import asyncio
from contextlib import asynccontextmanager
import uvicorn
from typing import Optional, Any, Callable
from fastapi import FastAPI,Form,File, UploadFile, HTTPException, Response, Security, status, Request
from fastapi.responses import JSONResponse
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.security import APIKeyHeader, APIKeyQuery

from io import BytesIO

import os
import tempfile
import aiofiles
import subprocess
import time 

# from parsers.pdf.parse_pdf import read_pdf
from parsers.embedder import docparser

from dotenv import load_dotenv

# Automatically load the .env file from the current directory or parent directories
load_dotenv()

# from src.db.pdb import Pgdb
# from src.emb.docz import DocEmbed

import logging 
log_ = logging.getLogger(__name__)

logFormatter = logging.Formatter("%(asctime)s [%(levelname)-5.5s] [%(filename)s:%(lineno)s - %(funcName)20s() ]    %(message)s")
consoleHandler = logging.StreamHandler(sys.stdout)
consoleHandler.setFormatter(logFormatter)
log_.addHandler(consoleHandler)
log_.setLevel(logging.DEBUG)

# https://www.sheshbabu.com/posts/fastapi-without-orm-getting-started-with-asyncpg

# logging.getLogger().addHandler(logging.StreamHandler(sys.stdout))
# consoleHandler.setFormatter(logFormatter)

log_ = logging.getLogger(__name__)
# import redis
# import debugpy
# debugpy.listen(("0.0.0.0",5677))
# debugpy.wait_for_client()
DB_NAME='embedding_db'
DB_HOST="192.168.3.164"
DB_PORT=5431
DB_USER_NAME="dev_user"
DB_PASSWORD="dev_password"

os.environ['PG_DATABASE'] = "embedding_db"
os.environ['PG_HOST'] = "192.168.3.164"
os.environ['PG_PORT'] = "5431"
os.environ['PG_USER'] = "dev_user"
os.environ['PG_PASSWORD'] = "dev_password"

API_KEYS = [
    "9d207bf0",
    "9d207bf0-10f5-4d8f-a479-22ff5aeff8d1",
    "f47d4a2c-24cf-4745-937e-620a5963c0b8",
    "b7061546-75e8-444b-a2c4-f19655d07eb8",
]

# api_key_header = APIKeyHeader(name="x-api-key", auto_error=False)
# def get_api_key(api_key_header: str = Security(api_key_header),) -> str:
#     """Retrieve and validate an API key from the query parameters or HTTP header.

#     Args:
#         api_key_query: The API key passed as a query parameter.
#         api_key_header: The API key passed in the HTTP header.

#     Returns:
#         The validated API key.

#     Raises:
#         HTTPException: If the API key is invalid or missing.
#     """
#     if api_key_header in API_KEYS:
#         return api_key_header
#     raise HTTPException(
#         status_code=status.HTTP_401_UNAUTHORIZED,
#         detail="Invalid or missing API Key",
#     )



# sdd = DocEmbed()
@asynccontextmanager
async def lifespan(app: FastAPI):
    # await sdd.adbconn()
    # await sdd.adbconnpool()
    yield
    # await sdd.adbclose()
    # await sdd.adbclosepool()


app = FastAPI(lifespan=lifespan)



# ------------------------------------------------------
# API key middleware
# ref: https://leapcell.io/blog/building-custom-middleware-in-fastapi-to-elevate-api-control
# ------------------------------------------------------
@app.middleware("http")
async def api_key_auth_middleware(request: Request, call_next):
    if request.url.path.startswith("/health"):
        # Allow access to public paths without API key
        response = await call_next(request)
        return response

    api_key = request.headers.get("x-api-key")
    if api_key in API_KEYS:
        response = await call_next(request)
        return response
    
    return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={"detail": "Unauthorized: Invalid or missing X-API-Key"}
            )

    # return JSONResponse(content={"api": False})
    # raise HTTPException(
    #     status_code=status.HTTP_401_UNAUTHORIZED,
    #     detail="Invalid or missing API Key",
    # )

    # if not api_key or api_key != SECRET_API_KEY:
    #     return JSONResponse(
    #         status_code=status.HTTP_401_UNAUTHORIZED,
    #         content={"detail": "Unauthorized: Invalid or missing X-API-Key"}
    #     )
    
    # response = await call_next(request)
    # return response


# odb = Pgdb(database=DB_NAME,host=DB_HOST,user=DB_USER_NAME,password=DB_PASSWORD,port=DB_PORT)
# odb = Pgdb()
# r = redis.Redis(host="redis", port=6379)
@app.get("/")
async def read_root():
    return {"Hello": "World-8ssd83"}

@app.get("/health")
async def read_root():
    start = time.monotonic()
    # # sdd = DocEmbed()
    # # isconn = await sdd.adbconn()
    # log_.info(f"db connection: {isconn}")
    # # isconn = await sdd.adbclose()
    # log_.info(f"db connection: {isconn}")
    # end = time.monotonic()
    # log_.info(f"Time taken: {end - start}")

    # -------------------------------------------
    # isconn = await sdd.adbconnpool()
    # log_.info(f"db connection: {isconn}")
    # isconn = await sdd.adbclosepool()
    # log_.info(f"db connection: {isconn}")
    end = time.monotonic()
    log_.info(f"Time taken: {end - start}")
    # print(isconn)
    # TODO close connection and log timing

    return {"Hello": "World-"}


@app.post("/pandoc")
async def run_pandoc(file: UploadFile = File(...),
                     srctype: str =Form("docx"),
                     desttype: str =Form("gfm"),):
    bSucess = False
    cat_list = []    
    try:
        # get file name
        file_name  = file.filename
        sanitize_file_name = str(file_name).replace(" ","_")
        with tempfile.TemporaryDirectory() as temp_dir:
            print(temp_dir)
            temp_file = temp_dir + os.sep + sanitize_file_name

            print(temp_file)
            async with aiofiles.open(temp_file, 'wb') as out_file:
                while content := await file.read(1024):  # async read chunk
                    await out_file.write(content)  # async write chunk    

            print("saved temp file")
            file.file.close()  
            out_file = temp_dir + os.sep + sanitize_file_name + ".md"

            # cmd = "pandoc " + temp_file + " -o " +  out_file
            # cmd = "pandoc " + temp_file + " -o " +  out_file
            log_.info(f"srcfile: {temp_file}")
            log_.info(f"destfile: {out_file}")
            cmd = f'pandoc -f {srctype} -t {desttype} {temp_file} -o {out_file}' 
            # Create a subprocess.Popen instance
            process = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

            # Wait for the command to complete and capture the output
            stdout, stderr = process.communicate()

            # Check the return code to see if the command succeeded
            return_code = process.returncode
            if return_code == 0:
                # print("ok")                
                path=out_file
                with open(path, "rb") as f:
                    data=f.read()                       
                    # read file and return contents back
                    memfile = BytesIO(data)
                    response = StreamingResponse(memfile, media_type="text/plain")
                    response.headers["Content-Disposition"] = f"inline; filename={sanitize_file_name}.md"

                    return response
            else:
                log_.error(f"pandoc return code: {return_code}, error msg:{stderr}")
                # return error in a json

    except Exception:
        raise HTTPException(status_code=500, detail='Something went wrong')
    finally:
        file.file.close()  


    if bSucess:
        return {"msg":"ok"}
    else: 
        return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={"detail": f"unable to process pandoc conversion. return code: {return_code}, error msg:{stderr} "}
            )



@app.post("/embed_doc")
async def perform_embedding(file: UploadFile = File(...),
                     srctype: str =Form("docx"),
                     desttype: str =Form("gfm"),):

    fname = file.filename 
    fmimetype = file.content_type
    fhead = file.headers
    fsize = file.size
    # sdd = DocEmbed()
    res= await docparser(fname,fsize,fmimetype,file)

    # isconn = await sdd.adbconn()
    # log_.info(f"db connection: {isconn}")
    # bret = await sdd.parse_document("/home")

    # print(isconn)
    # TODO close connection and log timing

    return {"Hello": "World-"}


@app.post("/query_doc")
async def query_embedding(querytext:str = Form(...)):

    # sdd = DocEmbed()

    print(f"{querytext}")
    # df_index, rc = await sdd.query_vector(querytext)
    # for index, row in df_index.iterrows():
    #     otext = str(row['TEXT'])
    #     oscore = str(row['score'])
    #     print(f"score: {oscore}, text: {otext}")

    # sql = "SELECT TEXT,(embedding <=> $1) as score FROM t_emb_1024 ORDER BY embedding <=> $1 DESC LIMIT $2"
    # df, rc = await sdd.asql_to_dataframe_two_param(sql,["TEXT","score"],querytext,3)
    # log_.info(f"row count: {rc}")
    # bret = await sdd.parse_document("/home")

    # print(isconn)
    # TODO close connection and log timing

    return {"Hello": "World-"}

# =============================================================
def run_async_task(func: Callable[...,Any], *args:Any,**kwargs: Any) -> None:
    """async function call for background tasks"""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(func(*args,**kwargs))
    finally:
        loop.close()
    
    return 


async def main():
    config = uvicorn.Config("main:app", host="0.0.0.0", port=8101, log_level="info", reload=True)
    server = uvicorn.Server(config)
    await server.serve()

if __name__ == "__main__":
    asyncio.run(main())    



