FROM nvcr.io/nvidia/pytorch:24.12-py3  
#FROM nvcr.io/nvidia/pytorch:23.12-py3

USER root
#--------------------------------------------------------------------------------
# upload easyocr model and sentence transformer model insider docker container
# latin_g2, english_g2 & craft_mlt_25k
#--------------------------------------------------------------------------------

ADD EasyOCR/model/. /EasyOCR/model

COPY easy_serve.py /workspace/
COPY req.txt .
# Install system dependencies
RUN pip3 install -r req.txt

#execute 
CMD ["python3", "/workspace/easy_serve.py"]