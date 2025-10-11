
import boto3


LOCAL_S3_PROXY_SERVICE_URL = 'http://192.168.3.164:9000'

s3_client = boto3.client('s3',aws_access_key_id="EJmZZD0aTifI0CIqb0K6",
                         aws_secret_access_key="8HQervIK3M5JczQNQhNnHjand8Eo2Xhg2W5SF4wL",
                         endpoint_url=LOCAL_S3_PROXY_SERVICE_URL,
                         use_ssl=False)
# Define the bucket name and prefix
bucket_name = 'bucketa'
paginator = s3_client.get_paginator('list_objects')
operation_parameters = {'Bucket': bucket_name,
                        'Prefix': 'ai-test_docs'}
page_iterator = paginator.paginate(**operation_parameters)  

response = s3_client.list_objects_v2(Bucket=bucket_name, Prefix='ai-test_docs', MaxKeys=10)
####
# Check if 'Contents' is in the response
if 'Contents' in response:
    for obj in response['Contents']:
        print(obj['Key'])
        # filename_list.append(obj['Key'])   
else:
    print(f"No files found .")
####
try:
    # Read an object from the bucket
    response = s3_client.get_object(Bucket=bucket_name, Key="6be6fb2edf3f4a04db8c0029394a159c")
    # Read the objects content as text
    img_data = response["Body"].read()#.decode("utf-8")    
    # img = cv2.imread(img_data, cv2.IMREAD_UNCHANGED)
    # file_stream = BytesIO()
    # # bucket.Object(key).download_fileobj(file_stream)
    # np_1d_array = np.frombuffer(img_data, dtype="uint8")
    # img = cv2.imdecode(np_1d_array, cv2.IMREAD_COLOR)
except Exception as e:
    print("ERROR: ",str(e))       
    
