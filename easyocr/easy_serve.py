import litserve as ls
import cv2
import numpy as np
import easyocr

import argparse
#import zfile 

parser = argparse.ArgumentParser()
parser.add_argument("-p", "--port", type=str, default="8041", help="listening port ")
parser.add_argument("-m", "--model", type=str, default="na", help="model name and full path ")	

args = parser.parse_args()    
model_name = args.model

def create_bounding_box(bbox_data):
    xs = []
    ys = []
    for x, y in bbox_data:
        xs.append(x)
        ys.append(y)
 
    left = int(min(xs))
    top = int(min(ys))
    right = int(max(xs))
    bottom = int(max(ys))
 
    return [left, top, right, bottom]
# (STEP 1) - DEFINE THE API (compound AI system)
class DocbeeLitAPI(ls.LitAPI):
    def setup(self, device):
        # self.pipeline = create_pipeline(pipeline='OCR',device='gpu:0')
        self.reader = easyocr.Reader(['en'], gpu=True)  # specify the language(s) 

    def decode_request(self, request, context):
        # return request["input"]
        files = request['files']#.stream.read()
        prompt = request['prompt']
        context['prompt'] = prompt
        # Preprocess the image
        files = request['files']#.stream.read()
        file_name  = files.filename
        
        # oget file conent as numpy array for cv2 read
        fx = np.fromstring(files.file.read(), np.uint8)
        img = cv2.imdecode(fx, cv2.IMREAD_UNCHANGED) #Image.open(files.file)
        (image_height, image_width,_) = img.shape             

        # context info for pipeline
        context['image_width'] = image_width
        context['image_height'] = image_height
        context['filename'] = file_name       
        return img          

    def predict(self, img_new, context):
        # Easily build compound systems. Run inference and return the output.
                # Use OCR to extract text from the image
        result  = self.reader.readtext(np.array(img_new), detail=1,batch_size=4)    
        outj = []
        for (bbox, text, prob) in result:
            # print(f"Text: {text}, Confidence: {prob}, Bounding Box: {bbox}")
            # outj = [{"txt": str(text), "bbox": create_bounding_box(bbox), "confidence": prob.item()}]   
            # outj.append({"txt": str(text), "bbox": create_bounding_box(bbox), "confidence": prob.item()})         
            outj.append({"txt": str(text), "bbox": create_bounding_box(bbox)})         
        # res = json.dumps(outj)
        return outj

    def encode_response(self, res,context):
        # Convert the model output to a response payload.
        filename = context['filename'] 
        img_width = context['image_width'] 
        img_height = context['image_height']         
        
        outjson = {
            "filename" : filename,
            "image_width": img_width,
            "image_height": img_height,
            "predicted_result": res
        }        
        return outjson

# (STEP 2) - START THE SERVER
if __name__ == "__main__":
    # scale with advanced features (batching, GPUs, etc...)
    api = DocbeeLitAPI(max_batch_size=1, batch_timeout=5)
    server = ls.LitServer(api, accelerator="gpu")
    server.run(port=args.port)