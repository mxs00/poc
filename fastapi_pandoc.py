import asyncio
from typing import Optional, Any, Callable
from fastapi import FastAPI,Form,FastAPI,File, UploadFile, HTTPException,Response
from starlette.applications import Starlette
# from starlette.responses import FileResponse
from fastapi.responses import FileResponse, StreamingResponse
from io import BytesIO

import os
import tempfile
import aiofiles
import subprocess

import redis

app = FastAPI()

import debugpy
debugpy.listen(("0.0.0.0",5678))
# debugpy.wait_for_client()


r = redis.Redis(host="redis", port=6379)
@app.get("/")
async def read_root():
    return {"Hello": "World43"}


@app.get("/items/{item_id}")
async def read_item(item_id: int, q: Optional[str] = None):
    return {"item_id": item_id, "q": q}


@app.get("/hits")
async def read_redis():
    r.incr("hits")
    return {"hello":r.get("hits")}


@app.post("/pandoc")
async def run_pandoc(file: UploadFile = File(...)):
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
            # result = subprocess.run(['pandoc', temp_file, '-o', out_file], stdout=subprocess.PIPE, stderr=subprocess.PIPE)       
            # result1 = subprocess.check_output('pandoc ' + temp_file + ' -o ' +  out_file, shell=True, text=True)                        

            # cmd = "pandoc " + temp_file + " -o " +  out_file
            # cmd = "pandoc " + temp_file + " -o " +  out_file
            cmd = 'pandoc -f docx -t markdown ' + temp_file + ' -o ' +  out_file + '' 
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
                    response.headers["Content-Disposition"] = f"inline; filename={sanitize_file_name + ".md"}"

                    return response
            else:
                print("fail")
                # return error in a json


            # # Print the captured output and return code
            # print("Standard Output:")
            # print(stdout.decode("utf-8"))
            # print("Standard Error:")
            # print(stderr.decode("utf-8"))
            # print(f"Return Code: {return_code}")


        # print(cat_list)
    except Exception:
        raise HTTPException(status_code=500, detail='Something went wrong')
    finally:
        file.file.close()  

    r.incr("hits")
    return {"hellccco":r.get("hits")}



def run_async_task(func: Callable[...,Any], *args:Any,**kwargs: Any) -> None:
    """async function call for background tasks"""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(func(*args,**kwargs))
    finally:
        loop.close()
    
    return 



