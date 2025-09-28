import psycopg2
import pandas as pd
from dateutil import parser
import locale
 
#  using '/media/ms/DATA2/data/donut_bcerts/trained_model/m_10' categorised on Aprl 6, 2025
def handle_multiple_dots(sval:str):
    dot_count = sval.count('.')    
    fstr = ''
    if dot_count <= 1:
        fstr = sval
    else:
        slt = sval.split('.')
        cnt_arr = len(slt)
        for idx, x in enumerate(slt):
            if idx == (cnt_arr - 1):        
                print('skip me')
                fstr = fstr + '.' + x
            else:
                fstr = fstr + x
    return fstr


class DatabaseHandler:
    def __init__(self, database: str, host: str, user: str, password: str, port: str):
        self.is_connected = False
        try:
            zoom = 1
            self.conn = psycopg2.connect(database=database,host=host,user=user,password=password,port=port)            
            self.is_connected = True  
            print("Connection to the database established successfully.")    
        except Exception as e:
            print('ERROR: Unable to connect to database:  ' + str(e))  
            self.is_connected = False

    def clean_USD(self,sval:str):

        rval = sval.replace('-','')
        rval = rval.replace('USD','')
        rval = rval.replace('$','')
        # handle multiple . dot in numbers i.e. 4.321.00 
        rval = handle_multiple_dots(rval)

        return rval
    
    def upsert_spliter_by_page(self, file_id:str, pdf_page_num:str,filename:str, path_with_filename:str):
        query = "INSERT INTO t_split_processor_v2 (file_id,pdf_page_num,filename,path_with_filename) VALUES (%s,%s,%s,%s) ON CONFLICT DO NOTHING;"
        # Create a cursor object to execute queries
        self.conn.autocommit = True
        cursor = self.conn.cursor()
        cursor.execute(query, (file_id,pdf_page_num,filename,path_with_filename))
        # Close the cursor and connection
        cursor.close()
        return        
    
    def upsert_prompts_file(self, modelname:str, classname:str,field:str, tag:str, prompt_txt:str):
        query = "INSERT INTO t_que_prompts (modelname,classname,field,tag,prompt) VALUES (%s,%s,%s,%s,%s) ON CONFLICT DO NOTHING;"
        # Create a cursor object to execute queries
        self.conn.autocommit = True
        cursor = self.conn.cursor()
        cursor.execute(query, (modelname,classname,field,tag,prompt_txt))
        # Close the cursor and connection
        cursor.close()
        return      

    # def upsert_file_in_index(self, file_path: str,num_pages:str):

    #     query = "INSERT INTO t_index (path_and_filename,status_overall,num_pages) VALUES (%s,%s,%s) ON CONFLICT DO NOTHING;"
    #     # Create a cursor object to execute queries
    #     self.conn.autocommit = True
    #     cursor = self.conn.cursor()
    #     cursor.execute(query, (file_path,'INITIAL',num_pages,))
    #     # Close the cursor and connection
    #     cursor.close()
    #     return
    
    def upsert_googledrive_files_in_index(self, parent_path:str, parentid:str,file_name: str,file_id:str,file_mimetype:str):
        query = "INSERT INTO t_index_v1 (file_id,parent_id,parent_path,filename,mime_type,status_overall) VALUES (%s,%s,%s,%s,%s,%s) ON CONFLICT DO NOTHING;"
        # Create a cursor object to execute queries
        self.conn.autocommit = True
        cursor = self.conn.cursor()
        cursor.execute(query, (file_id,parentid,parent_path,file_name,file_mimetype,'INITIAL'))
        # Close the cursor and connection
        cursor.close()
        return    
    
    def upsert_aws_folder_in_index(self, folder:str, filename:str):
        '''new record in index table update'''
        query = "INSERT INTO t_que_index (folder,filename,status_overall) VALUES (%s,%s,%s) ON CONFLICT DO NOTHING;"
        # Create a cursor object to execute queries
        self.conn.autocommit = True
        cursor = self.conn.cursor()
        cursor.execute(query, (folder,filename,'INITIAL'))
        # Close the cursor and connection
        cursor.close()
        return    
    
    def update_file_category(self, file_id: str, new_status: str, fld_category:str = 'category'):
        '''index table update'''

        query = "UPDATE t_que_index SET " + fld_category + " = (%s),step_flag_2 = 'X'  where qid = (%s)"
        # Create a cursor object to execute queries
        cursor = self.conn.cursor()
        cursor.execute(query, (new_status,file_id,))
        # Close the cursor and connection
        cursor.close()
        self.conn.commit()        
        return 
       
    def bulk_status_update(self):
        ''' step_flag_1: C=completed, E=extraction - categories that can be used for rtdetr field extraction
        '''        

        qry = "UPDATE t_que_index SET step_flag_1 = NULL"
        self.update_bulk(qry)

        qry = "UPDATE t_que_index SET step_flag_1 = 'C' where category IS NOT NULL"
        self.update_bulk(qry)        

        qry = "UPDATE t_que_index SET step_flag_1 = 'E' where category IN ('bcert_type3','bcert_type4')"
        self.update_bulk(qry)        

        return
    

    def get_file_id(self, filename:str): 
        file_id = ''
        query = "SELECT qid FROM t_que_index WHERE filename = %s"                         
        df_index = self.sql_to_dataframe_single_param(query , ['qid'],filename)
        rows_count = len(df_index.index)
        for index, row in df_index.iterrows():
            file_id = str(row['qid'])
            break
            # get loan attributes
        return file_id, rows_count
    
    def get_file_id_usingfolder(self, folder_name:str, filename:str): 
        file_id = ''
        query = "SELECT qid FROM t_que_index WHERE folder = %s and filename = %s "                         
        df_index = self.sql_to_dataframe_two_param(query , ['qid'],folder_name, filename)
        rows_count = len(df_index.index)
        for index, row in df_index.iterrows():
            file_id = str(row['qid'])
            break
            # get loan attributes
        return file_id, rows_count

    def get_allfiles_from_index(self, filename:str): 
        file_id = ''
        # query = "SELECT qid,folder,filename,category FROM t_que_index WHERE step_flag_2 IN ('X') ORDER BY folder,filename"                         
        # query = "SELECT qid,folder,filename,category FROM t_que_index WHERE filename like '%affidavit_cropped.png' ORDER BY folder,filename"       
        # query = "SELECT qid,folder,filename,category FROM t_que_index ORDER BY folder,filename"      
        # query = "SELECT qid,folder,filename,category FROM t_que_index WHERE category in ('bcert_type2_frm4','bcert_type2_frm2','bcert2_type2_frm4','bcert_type5') ORDER BY folder,filename"                                 
        query = "SELECT qid,folder,filename,category FROM t_que_index WHERE category in ('bcert_type3') ORDER BY folder,filename"                                         
        df_index = self.sql_to_dataframe(query , ['qid','folder','filename','category'])
        rows_count = len(df_index.index)
        # for index, row in df_index.iterrows():
        #     file_id = str(row['qid'])
        #     break
        #     # get loan attributes
        return df_index, rows_count

    def get_allfiles_from_index_for_cat(self, ctype:str): 
        file_id = ''
        # query = "SELECT qid,folder,filename,category FROM t_que_index WHERE step_flag_2 IN ('X') ORDER BY folder,filename"                         
        # query = "SELECT qid,folder,filename,category FROM t_que_index WHERE filename like '%affidavit_cropped.png' ORDER BY folder,filename"       
        # query = "SELECT qid,folder,filename,category FROM t_que_index ORDER BY folder,filename"      
        # query = "SELECT qid,folder,filename,category FROM t_que_index WHERE category in ('bcert_type2_frm4','bcert_type2_frm2','bcert2_type2_frm4','bcert_type5') ORDER BY folder,filename"                                 
        # query = "SELECT qid,folder,filename,category FROM t_que_index WHERE category in ('" + ctype + "') ORDER BY folder,filename"   
        # query = "SELECT qid,folder,filename,category,category_rev FROM t_que_index WHERE " + ctype + " ORDER BY folder,filename"                                                 
        # query = "SELECT qid,folder,filename,category,sub_cat1 as category_rev FROM t_que_index WHERE " + ctype + " ORDER BY folder,filename"                                                         
        query = "SELECT qid,folder,filename,category,sub_cat1 as category_rev FROM t_que_index WHERE " + ctype + " ORDER BY folder,filename"                                                                 
        df_index = self.sql_to_dataframe(query , ['qid','folder','filename','category','category_rev'])
        rows_count = len(df_index.index)
        # for index, row in df_index.iterrows():
        #     file_id = str(row['qid'])
        #     break
        #     # get loan attributes
        return df_index, rows_count

    def get_all_from_index_for_vectordb(self): 
        file_id = ''
        # query = "SELECT qid,folder,filename,category FROM t_que_index ORDER BY folder,filename"                         
        # query = "SELECT qid,folder,filename,category FROM t_que_index where category in ('amendment_type1') ORDER BY folder,filename"  # 2,474   
        
        # bcert2_type2_frm4 + bcert_type2_frm2 = 631 + 267 = 898
        # query = "SELECT qid,folder,filename,category FROM t_que_index where category in ('bcert_type2_frm2','bcert2_type2_frm4') ORDER BY folder,filename" # 898  

        # query = "SELECT qid,folder,filename,category FROM t_que_index where category in ('bcert_type2_frm1') ORDER BY folder,filename" # 421  
        # query = "SELECT qid,folder,filename,category FROM t_que_index where category in ('bcert_type5') ORDER BY folder,filename" # 34  
        query = "SELECT qid,folder,filename,category,affidavit_cat,sub_cat1 FROM t_que_index where category in ('affidavit_type1') and affidavit_cat in ('bcert_type8') ORDER BY folder,filename" # 34  
        query = "SELECT qid,folder,filename,category,affidavit_cat,sub_cat1 FROM t_que_index where category in ('bcert_type8') and sub_cat1 in ('bcert_type5_fld22') ORDER BY folder,filename" # 34  
        query = "SELECT qid,folder,filename,category,affidavit_cat,sub_cat1 FROM t_que_index where category IN ('bcert_type3','bcert_type4') ORDER BY folder,filename" # 34          

        df_index = self.sql_to_dataframe(query , ['qid','folder','filename','category','affidavit_cat','sub_cat1'])
        rows_count = len(df_index.index)
        # for index, row in df_index.iterrows():
        #     file_id = str(row['qid'])
        #     break
        #     # get loan attributes
        return df_index, rows_count

    def get_filterd_index_for_vectordb(self,category:str,sub_cat:str): 
        file_id = ''
        # query = "SELECT qid,folder,filename,category FROM t_que_index ORDER BY folder,filename"                         
        # query = "SELECT qid,folder,filename,category FROM t_que_index where category in ('amendment_type1') ORDER BY folder,filename"  # 2,474   
        
        # bcert2_type2_frm4 + bcert_type2_frm2 = 631 + 267 = 898
        # query = "SELECT qid,folder,filename,category FROM t_que_index where category in ('bcert_type2_frm2','bcert2_type2_frm4') ORDER BY folder,filename" # 898  

        # query = "SELECT qid,folder,filename,category FROM t_que_index where category in ('bcert_type2_frm1') ORDER BY folder,filename" # 421  
        # query = "SELECT qid,folder,filename,category FROM t_que_index where category in ('bcert_type5') ORDER BY folder,filename" # 34  
        query = "SELECT qid,folder,filename,category,affidavit_cat FROM t_que_index where category in ('affidavit_type1') and affidavit_cat in ('bcert_type8') ORDER BY folder,filename" # 34  
        query = "SELECT qid,folder,filename,category,affidavit_cat,sub_cat1 FROM t_que_index where category in ('" + category + "') and sub_cat1 in ('" + sub_cat + "') ORDER BY folder,filename" # 34  

        df_index = self.sql_to_dataframe(query , ['qid','folder','filename','category','affidavit_cat','sub_cat1'])
        rows_count = len(df_index.index)
        # for index, row in df_index.iterrows():
        #     file_id = str(row['qid'])
        #     break
        #     # get loan attributes
        return df_index, rows_count


    def get_all_subcat_group_by_vectordb(self): 
        file_id = ''
        query = "SELECT category,sub_cat1, COUNT(1) as cnt FROM t_que_index where category like 'bcert_type2%' GROUP BY category,sub_cat1 ORDER BY category,sub_cat1" # 34  
        query = "select category,sub_cat1, COUNT(1) from t_que_index WHERE processed_flag IS NULL AND category IN ('bcert_type3','bcert_type4') GROUP BY category,sub_cat1 ORDER BY category,sub_cat1" # 34  
        query = "SELECT category,sub_cat1, COUNT(1) as cnt FROM t_que_index where category in ('bcert_type2_frm2') GROUP BY category,sub_cat1 ORDER BY category,sub_cat1" # 34  
        query = "SELECT category,sub_cat1, COUNT(1) as cnt FROM t_que_index where category in ('affidavit_type2','affidavit_type3','affidavit_type4') GROUP BY category,sub_cat1 ORDER BY category,sub_cat1" # 34          

        df_index = self.sql_to_dataframe(query , ['category','sub_cat1','cnt'])
        rows_count = len(df_index.index)
        # for index, row in df_index.iterrows():
        #     file_id = str(row['qid'])
        #     break
        #     # get loan attributes
        return df_index, rows_count


    def get_all_from_index(self): 
        file_id = ''
        # query = "SELECT qid,folder,filename,category FROM t_que_index ORDER BY folder,filename"                         
        # query = "SELECT qid,folder,filename,category FROM t_que_index where category in ('amendment_type1') ORDER BY folder,filename"  # 2,474   
        
        # bcert2_type2_frm4 + bcert_type2_frm2 = 631 + 267 = 898
        # query = "SELECT qid,folder,filename,category FROM t_que_index where category in ('bcert_type2_frm2','bcert2_type2_frm4') ORDER BY folder,filename" # 898  

        # query = "SELECT qid,folder,filename,category FROM t_que_index where category in ('bcert_type2_frm1') ORDER BY folder,filename" # 421  
        # query = "SELECT qid,folder,filename,category FROM t_que_index where category in ('bcert_type5') ORDER BY folder,filename" # 34  
        # query = "SELECT qid,folder,filename,category FROM t_que_index where category in ('affidavit_type1','affidavit_type2','affidavit_type3') ORDER BY folder,filename" # 34  
        query = "SELECT qid,folder,filename,category FROM t_que_index where category in ('affidavit_type1','affidavit_type2','affidavit_type3')  AND processed_flag IS NULL ORDER BY folder,filename" # 34  

        df_index = self.sql_to_dataframe(query , ['qid','folder','filename','category'])
        rows_count = len(df_index.index)
        # for index, row in df_index.iterrows():
        #     file_id = str(row['qid'])
        #     break
        #     # get loan attributes
        return df_index, rows_count


    def upsert_json_file_index(self, file_id:str,jtype:str,status:str):
        query = "INSERT INTO t_que_json (jid,jtype,status) VALUES (%s,%s,%s) ON CONFLICT DO NOTHING;"
        # Create a cursor object to execute queries
        cursor = self.conn.cursor()
        cursor.execute(query, (file_id,jtype,status,))
        # Close the cursor and connection
        cursor.close()
        self.conn.commit()             
        return     
    
    def reset_processing_que_with_abandaned_entries(self, jtype:str,status:str):
        ''' reset status of hanged items in que that have been in PROCESSING state from more that 300 seconds'''

        query = """UPDATE t_que_json SET status = 'INITIAL', ts_start=NULL, ts_end=NULL,ts_duration=NULL,agent_name=NULL WHERE jtype =%s 
AND jid IN (	
SELECT jid FROM t_que_json  
WHERE status = %s 
AND jtype = %s  
AND (EXTRACT(epoch FROM CURRENT_TIMESTAMP) - EXTRACT(epoch FROM ts_start)) > 300
)"""
        # Create a cursor object to execute queries
        cursor = self.conn.cursor()
        cursor.execute(query, (jtype, status, jtype,))
        # Close the cursor and connection
        cursor.close()
        self.conn.commit()             
        return         

    def update_json(self,file_id:str,jtype:str,json_string:str):
        query = """UPDATE t_que_json SET json_string = %s WHERE jid=%s and jtype=%s """
        # Create a cursor object to execute queries
        cursor = self.conn.cursor()
        cursor.execute(query, (json_string,file_id,jtype,))
        # Close the cursor and connection
        cursor.close()
        self.conn.commit()        
        return  
    def update_agent_name(self,file_id:str,agent_name:str):
        query = """UPDATE t_que_json SET agent_name = %s WHERE jid=%s"""
        # Create a cursor object to execute queries
        cursor = self.conn.cursor()
        cursor.execute(query, (agent_name,file_id,))
        # Close the cursor and connection
        cursor.close()
        self.conn.commit()        
        return  
    def update_json_status(self,file_id:str,jtype:str, status:str):
        query = "UPDATE t_que_json SET status =%s WHERE jid=%s AND jtype=%s"
        # Create a cursor object to execute queries
        cursor = self.conn.cursor()
        cursor.execute(query, (status,file_id,jtype,))
        # Close the cursor and connection
        cursor.close()
        self.conn.commit()        
        return  
    def update_json_set_status_with_start_timestamp(self,file_id:str,jtype:str,status:str):
        query = "UPDATE t_que_json SET status=%s, ts_start=CURRENT_TIMESTAMP, ts_end=NULL,ts_duration=NULL WHERE jid=%s AND jtype=%s"
        # Create a cursor object to execute queries
        cursor = self.conn.cursor()
        cursor.execute(query, (status,file_id,jtype,))
        # Close the cursor and connection
        cursor.close()
        self.conn.commit()        
        return  
    def update_json_set_apitag(self,file_id:str,jtype:str,apitag:str,agent_name:str):
        query = "UPDATE t_que_json SET apitag=%s,agent_name=%s  WHERE jid=%s AND jtype=%s"
        # Create a cursor object to execute queries
        cursor = self.conn.cursor()
        cursor.execute(query, (apitag,agent_name,file_id,jtype,))
        # Close the cursor and connection
        cursor.close()
        self.conn.commit()        
        return      
    def update_json_set_status_with_end_timestamp(self,file_id:str,jtype:str,status:str):
        query = "UPDATE t_que_json SET status=%s, ts_end=CURRENT_TIMESTAMP,ts_duration=EXTRACT(SECOND FROM (CURRENT_TIMESTAMP - ts_start)) WHERE jid=%s AND jtype=%s"
        # Create a cursor object to execute queries
        cursor = self.conn.cursor()
        cursor.execute(query, (status,file_id,jtype,))
        # Close the cursor and connection
        cursor.close()
        self.conn.commit()        
        return 

    def get_files_df_not_ocr(self,folder:str,qtype:str): 
        ''' get files that need to be ocr'''

        query = """SELECT qid FROM t_que_index WHERE folder IN (%s) AND step_flag_1 IN ('A')
              EXCEPT 
                SELECT jid AS qid FROM t_que_json WHERE jtype = %s
                AND jid in ( 
                    SELECT qid FROM t_que_index WHERE folder IN (%s) AND step_flag_1 IN ('A')
                    )
            LIMIT 1000 """
        
        df_index = self.sql_to_dataframe_three_param(query , ['qid'],folder,qtype,folder)
        rows_count = len(df_index.index)

        return df_index, rows_count
    
    def get_files_df_not_ocr_all(self,qtype:str): 
        ''' get files that need to be ocr'''

        query = """SELECT qid FROM t_que_index WHERE step_flag_1 IN ('A')
              EXCEPT 
                SELECT jid AS qid FROM t_que_json WHERE jtype = %s
                AND jid in ( 
                    SELECT qid FROM t_que_index WHERE step_flag_1 IN ('A')
                    )
             """
        
        df_index = self.sql_to_dataframe_single_param(query , ['qid'],qtype)
        rows_count = len(df_index.index)

        return df_index, rows_count    

    def get_json_que_by_status(self,folder:str,jtype:str,status:str): 
        ''' get files that need to be ocr based on status'''

        query = """SELECT jid AS qid FROM t_que_json WHERE jtype = %s AND status=%s """
        
        df_index = self.sql_to_dataframe_two_param(query , ['qid'],jtype,status)
        rows_count = len(df_index.index)

        return df_index, rows_count
    
    def bulkjson_by_status(self,folder:str,jtype:str,status:str,agentfilter:str,category:str,step_flag_1:str='E'): 
        ''' get files that need to be ocr based on status'''

        if folder == '':
            query = """SELECT jid,jtype,json_string FROM t_que_json WHERE jtype = %s AND status=%s 
    AND jid IN ( SELECT qid FROM t_que_index WHERE step_flag_1 IN ('""" + step_flag_1 + """') AND category in """ + category + """)"""
            df_index = self.sql_to_dataframe_two_param(query , ['jid','jtype','json_string'],jtype,status)            
        else:
            query = """SELECT jid,jtype,json_string FROM t_que_json WHERE jtype = %s AND status=%s 
    AND jid IN ( SELECT qid FROM t_que_index WHERE folder IN (%s) AND step_flag_1 IN ('""" + step_flag_1 + """') AND category in """ + category + """)"""
            df_index = self.sql_to_dataframe_three_param(query , ['jid','jtype','json_string'],jtype,status,folder)
        
        rows_count = len(df_index.index)

        return df_index, rows_count

    def get_single_file_by_status(self,jtype:str,status:str): 
        ''' get files that need to be ocr based on status'''

        jid = ''
        query = """SELECT jid FROM t_que_json WHERE jtype = %s AND status=%s LIMIT 1"""       
        df_index = self.sql_to_dataframe_two_param(query , ['jid'],jtype,status)
        rows_count = len(df_index.index)
        for index, row in df_index.iterrows():
            jid = str(row['jid'])

        return jid, rows_count

    def get_file_json_attributes(self, file_id:str,jtype:str): 

        jid = ''
        jtype = ''        
        status = ''
        status_http = ''        

        query = "SELECT jid, jtype, status, status_http FROM t_que_json WHERE jid = %s AND  jtype = %s"                         
        df_index = self.sql_to_dataframe_two_param(query , ['jid','jtype','status','status_http'],file_id,jtype)
        rows_count = len(df_index.index)

        # get json file cache attributes
        for index, row in df_index.iterrows():
            jid = str(row['jid'])
            jtype = str(row['jtype'])        
            status = str(row['status'])
            status_http = str(row['status_http'])                

        return rows_count,jid,jtype,status,status_http

    def get_prompts(self, field:str, classname:str, model:str,ocr_tag:str=''): 

        modelname = ''
        # field = ''
        prompt = ''        

        # query = "SELECT modelname, field, prompt FROM t_que_prompts WHERE field= %s and classname = %s and tag=%s and modelname=%s"                         
        query = "SELECT modelname, field, prompt FROM t_que_prompts WHERE field= %s and classname like '%%" + classname + "%%' and tag=%s and modelname=%s"                         
        # df_index = self.sql_to_dataframe_four_param(query , ['modelname','field','prompt'], field, classname,ocr_tag,model)
        df_index = self.sql_to_dataframe_three_param(query , ['modelname','field','prompt'], field, ocr_tag,model)        
        rows_count = len(df_index.index)

        # # get json file cache attributes
        for index, row in df_index.iterrows():
            modelname = str(row['modelname'])
            field = str(row['field'])        
            prompt = str(row['prompt'])
         

        return rows_count,modelname,field,prompt




    def get_file_index_attributes(self, file_id:str): 

        folder = ''
        filename = ''        
        category = ''

        query = "SELECT folder,filename, category FROM t_que_index WHERE qid = %s"                         
        df_index = self.sql_to_dataframe_single_param(query , ['folder','filename','category'],file_id)
        rows_count = len(df_index.index)

        # get json file cache attributes
        for index, row in df_index.iterrows():
            folder = str(row['folder'])
            filename = str(row['filename'])        
            category = str(row['category'])

        return rows_count,folder,filename,category
    
    def get_model_api_attributes(self, apitag:str): 

        model_name = ''
        url = ''        
        apikey = ''
        status = ''        

        query = "SELECT model_name, url, apikey, status FROM t_que_api_config WHERE apitag = %s and status='ACTIVE'"                         
        df_index = self.sql_to_dataframe_single_param(query , ['model_name','url','apikey','status'],apitag,)
        rows_count = len(df_index.index)

        # get json file cache attributes
        for index, row in df_index.iterrows():
            model_name = str(row['model_name'])
            url = str(row['url'])        
            apikey = str(row['apikey'])
            status = str(row['status'])                

        return rows_count,model_name,url,apikey,status


    def get_json_string_by_type(self,file_id:str,jtype:str):     
        json_string = ''
        query = "SELECT json_string FROM t_que_json WHERE jid=%s and jtype=%s" 
        df_index = self.sql_to_dataframe_two_param(query , ['json_string'],file_id,jtype)
        rows_count = len(df_index.index)
        for index, row in df_index.iterrows():
            json_string = row['json_string']        
        return json_string,rows_count
    # ---------------------------------------------------------

    def update_split_page_type(self, file_id: str, pdf_page_num: str,type:str,confidence:str):

        query = "UPDATE t_split_processor_v2 SET type = (%s),confidence = (%s)  where file_id = (%s) and pdf_page_num = (%s);"
        # Create a cursor object to execute queries

        cursor = self.conn.cursor()
        cursor.execute(query, (type,confidence,file_id,pdf_page_num,))
        # Close the cursor and connection
        cursor.close()
        self.conn.commit()
        return  

    def update_types_count_in_index_table(self):

        query = "UPDATE t_index_v1 SET num_types = (SELECT count(distinct(types)) FROM t_split_processor_v1 WHERE t_split_processor_v1.file_id = t_index_v1.file_id)"
        # Create a cursor object to execute queries
        cursor = self.conn.cursor()
        cursor.execute(query)
        # Close the cursor and connection
        cursor.close()
        self.conn.commit()   

        query = "UPDATE t_index_v1 SET types_list = (SELECT string_agg(DISTINCT(types), ', ') AS res FROM t_split_processor_v1 WHERE t_split_processor_v1.file_id = t_index_v1.file_id )"
        # Create a cursor object to execute queries
        cursor = self.conn.cursor()
        cursor.execute(query)
        # Close the cursor and connection
        cursor.close()
        self.conn.commit()   





        return    

    def update_unhandled_mimetypes_set_status(self):

        query = "UPDATE t_index_v1 SET status_overall = 'UNHANDLED_MIMETYPE' WHERE mime_type not IN ('application/pdf','application/vnd.google-apps.folder','text/xml')"
        # Create a cursor object to execute queries
        cursor = self.conn.cursor()
        cursor.execute(query)
        # Close the cursor and connection
        cursor.close()
        self.conn.commit()        
        return    
    
    def insert_file_classifcation(self, file_id: str, df_class: pd.DataFrame):
        query = "INSERT INTO t_split_processor (file_id,types,confidence,pages) VALUES (%s,%s,%s,%s) ON CONFLICT DO NOTHING;"
        # Create a cursor object to execute queries
        self.conn.autocommit = True
        cursor = self.conn.cursor()
        # save dataframe rows in database
        for index, row in df_class.iterrows():
            classification = row['Classification']
            confidence = row['Confidence']
            pages = row['Pages']            
            cursor.execute(query, (file_id,classification,confidence,pages))

        # Close the cursor and connection
        cursor.close()
        self.conn.commit()        
        return           
    def insert_file_classifcation_v1(self, file_id: str, df_class: pd.DataFrame):
        query = "INSERT INTO t_split_processor_v1 (file_id,types,confidence,pages) VALUES (%s,%s,%s,%s) ON CONFLICT DO NOTHING;"
        # Create a cursor object to execute queries
        cursor = self.conn.cursor()
        # df = pd.DataFrame({"Classification": types, "Confidence": confidence, "Pages": pages})
        for index, row in df_class.iterrows():
            classification = row['Classification']
            confidence = row['Confidence']
            pages = row['Pages']            
            cursor.execute(query, (file_id,classification,confidence,pages))

        # Close the cursor and connection
        cursor.close()
        self.conn.commit()             
        return  
    def upsert_json_file(self, file_id:str):
        query = "INSERT INTO t_index_json_v1 (file_id) VALUES (%s) ON CONFLICT DO NOTHING;"
        # Create a cursor object to execute queries
        cursor = self.conn.cursor()
        cursor.execute(query, (file_id,))
        # Close the cursor and connection
        cursor.close()
        self.conn.commit()             
        return     
     
    def update_json_string(self,file_id:str,json_string:str):
        query = "UPDATE t_index_json_v1 SET json_string = %s WHERE file_id=%s"
        # Create a cursor object to execute queries
        cursor = self.conn.cursor()
        cursor.execute(query, (json_string,file_id,))
        # Close the cursor and connection
        cursor.close()
        self.conn.commit()        
        return  


    def delete_fulltable(self, tablename: str):
        query = "DELETE from " + tablename + ""
        # Create a cursor object to execute queries
        cursor = self.conn.cursor()
        cursor.execute(query,)
        # Close the cursor and connection
        cursor.close()
        self.conn.commit()        
        return 


    def delete_specalized_processor_data(self, file_id: str):
        query = "DELETE from t_processor_v1 where file_id = %s"
        # Create a cursor object to execute queries
        cursor = self.conn.cursor()
        cursor.execute(query, (file_id,))
        # Close the cursor and connection
        cursor.close()
        self.conn.commit()        
        return 
    
    def delete_compliance_results_by_date(self, run_date: str):
        query = "delete FROM t_compliance_v2 WHERE run_date = %s"
        # Create a cursor object to execute queries
        cursor = self.conn.cursor()
        cursor.execute(query, (run_date,))
        # Close the cursor and connection
        cursor.close()
        self.conn.commit()        
        return 




    def upsert_norm_record(self, file_id: str,tbl_name:str):
        query = "INSERT INTO " + tbl_name + " (file_id) VALUES (%s) ON CONFLICT DO NOTHING;"

        # Create a cursor object to execute queries
        cursor = self.conn.cursor()
        cursor.execute(query, (file_id,))
        # Close the cursor and connection
        cursor.close()
        self.conn.commit()        
        return    

    def update_index_table_attribute(self,file_id: str,column_name:str,val:str,table_name:str):

        query = "UPDATE " + table_name + " SET " + column_name + " = %s WHERE file_id=%s"
        # Create a cursor object to execute queries
        cursor = self.conn.cursor()
        cursor.execute(query, (val,file_id,))
        # Close the cursor and connection
        cursor.close()
        self.conn.commit()        
        return  

    def update_bulk(self,query: str):
        # Create a cursor object to execute queries
        cursor = self.conn.cursor()
        cursor.execute(query)
        # Close the cursor and connection
        cursor.close()
        self.conn.commit()        
        return 
 
    def sql_to_dataframe(self, query,column_names):
        # “”” 
        # Import data from a PostgreSQL database using a SELECT query 
        # “””
        cursor = self.conn.cursor()
        try:
            cursor.execute(query)
        except (Exception, psycopg2.DatabaseError) as error:
            print('Error: %s' % error)
            cursor.close()
            return 1
        # The execute returns a list of tuples:
        tuples_list = cursor.fetchall()
        cursor.close()
        # Now we need to transform the list into a pandas DataFrame:
        df = pd.DataFrame(tuples_list, columns=column_names)
        return df   
    
    def sql_to_dataframe_single_param(self, query,column_names, val:str):
        # “”” 
        # Import data from a PostgreSQL database using a SELECT query 
        # “””
        cursor = self.conn.cursor()
        try:
            cursor.execute(query, (val,))
        except (Exception, psycopg2.DatabaseError) as error:
            print('Error: %s' % error)
            cursor.close()
            return 1
        # The execute returns a list of tuples:
        tuples_list = cursor.fetchall()
        cursor.close()
        # Now we need to transform the list into a pandas DataFrame:
        df = pd.DataFrame(tuples_list, columns=column_names)
        return df   
    def sql_to_dataframe_two_param(self, query,column_names, val1:str, val2:str):
        # “”” 
        # Import data from a PostgreSQL database using a SELECT query 
        # “””
        cursor = self.conn.cursor()
        try:
            cursor.execute(query, (val1,val2,))
        except (Exception, psycopg2.DatabaseError) as error:
            print('Error: %s' % error)
            cursor.close()
            return 1
        # The execute returns a list of tuples:
        tuples_list = cursor.fetchall()
        cursor.close()
        # Now we need to transform the list into a pandas DataFrame:
        df = pd.DataFrame(tuples_list, columns=column_names)
        return df   
    def sql_to_dataframe_three_param(self, query,column_names, val1:str, val2:str,val3:str):
        # “”” 
        # Import data from a PostgreSQL database using a SELECT query 
        # “””
        cursor = self.conn.cursor()
        try:
            cursor.execute(query, (val1,val2,val3,))
        except (Exception, psycopg2.DatabaseError) as error:
            print('Error: %s' % error)
            cursor.close()
            return 1
        # The execute returns a list of tuples:
        tuples_list = cursor.fetchall()
        cursor.close()
        # Now we need to transform the list into a pandas DataFrame:
        df = pd.DataFrame(tuples_list, columns=column_names)
        return df   
    def sql_to_dataframe_four_param(self, query,column_names, val1:str, val2:str,val3:str,val4:str):
        # “”” 
        # Import data from a PostgreSQL database using a SELECT query 
        # “””
        cursor = self.conn.cursor()
        try:
            cursor.execute(query, (val1,val2,val3,val4,))
        except (Exception, psycopg2.DatabaseError) as error:
            print('Error: %s' % error)
            cursor.close()
            return 1
        # The execute returns a list of tuples:
        tuples_list = cursor.fetchall()
        cursor.close()
        # Now we need to transform the list into a pandas DataFrame:
        df = pd.DataFrame(tuples_list, columns=column_names)
        return df   


    def sync_que_json_table(self, jtype:str):
        ''' syncronise json table with que table for processing'''

        # reset processing for more that 300 seconds
        self.reset_processing_que_with_abandaned_entries(jtype,'PROCESSING')
        
        # # sync index with processing table 
        # df_initial, rowcount_initial = self.get_files_df_not_ocr('Birth Records 119604/160001-165000/',jtype)
        df_initial, rowcount_initial = self.get_files_df_not_ocr_all(jtype)

        # get files with no ocr
        for index, row in df_initial.iterrows():
            file_id = str(row['qid'])
            self.upsert_json_file_index(file_id,jtype,'INITIAL')

        return    
    # -----------------------------------------------
    # status field generic functions
    # -----------------------------------------------
    def update_file_index_set_field_status_with_start_timestamp(self,file_id:str,status_fld:str,status:str):
        query = "UPDATE t_que_index SET " + status_fld + "=%s, skew_ts_start=CURRENT_TIMESTAMP, skew_ts_end=NULL WHERE qid=%s "
        # Create a cursor object to execute queries
        cursor = self.conn.cursor()
        cursor.execute(query, (status,file_id,))
        # Close the cursor and connection
        cursor.close()
        self.conn.commit()         

    def get_single_t_que_index_row_by_status(self,status_fld:str,rtdetr_status:str='UPLOADED'): 
        ''' get files that need to be ocr based on status'''

        out_folder = ''
        out_filename = ''
        out_file_id = ''      
        out_category = ''
          
        query = """SELECT qid,folder,filename,category FROM t_que_index WHERE """ + status_fld + """=%s 
        LIMIT 1"""       
        df_index = self.sql_to_dataframe_single_param(query , ['qid','folder','filename','category'],rtdetr_status)
        rows_count = len(df_index.index)
        for index, row in df_index.iterrows():
            out_folder = str(row['folder'])
            out_filename = str(row['filename'])
            out_file_id = str(row['qid'])            
            out_category = str(row['category'])            

        return out_file_id,out_folder,out_filename, out_category, rows_count   

    def update_file_index_field_status_with_end_timestamp(self,file_id:str,status_fld:str,status:str):
        query = "UPDATE t_que_index SET " + status_fld + "=%s, skew_ts_end=CURRENT_TIMESTAMP WHERE qid=%s"
        # Create a cursor object to execute queries
        cursor = self.conn.cursor()
        cursor.execute(query, (status,file_id,))
        # Close the cursor and connection
        cursor.close()
        self.conn.commit()        
        return 

    def update_field(self,file_id:str,dbfld:str,value:str):
        query = """UPDATE t_que_index SET  """ + dbfld + """ = %s WHERE qid=%s """
        # Create a cursor object to execute queries
        cursor = self.conn.cursor()
        cursor.execute(query, (value,file_id))
        # Close the cursor and connection
        cursor.close()
        self.conn.commit()        
        return  
    def update_field_by_filename(self,filename:str,dbfld:str,value:str):
        query = """UPDATE t_que_index SET  """ + dbfld + """ = '""" + value + """' WHERE filename like '%""" + filename + """' """
        # Create a cursor object to execute queries
        cursor = self.conn.cursor()
        cursor.execute(query)
        # Close the cursor and connection
        cursor.close()
        self.conn.commit()        
        return  
# ===========================================================================
# ===========================================================================
class Transport_proc_data:
    # global static variables

    withdrawal_date = ''
    withdrawal_description = ''
    withdrawal_amt = ''
    deposit_date = ''
    deposit_description = ''
    deposit_amt = ''
    processor_id = ''

    
    def __init__(self,dbx:DatabaseHandler,file_id:str):
        self.dbx = dbx
        self.file_id = file_id

    def clear(self):
        self.withdrawal_date = ''
        self.withdrawal_description = ''
        self.withdrawal_amt = ''
        self.deposit_date = ''
        self.deposit_description = ''
        self.deposit_amt = ''        

    def update_table_attribute(self,column_name:str,val:str):

        query = "UPDATE t_table_item_transpose_v1 SET " + column_name + " = %s WHERE file_id=%s and processor_id=%s"
        # Create a cursor object to execute queries
        cursor = self.dbx.conn.cursor()
        cursor.execute(query, (val,self.file_id,self.processor_id,))
        # Close the cursor and connection
        cursor.close()
        self.dbx.conn.commit()        
        return  


    def persist(self):
        query = "INSERT INTO t_table_item_transpose_v1 (file_id,processor_id) VALUES (%s,%s) ON CONFLICT DO NOTHING"
        # Create a cursor object to execute queries
        # self.dbx.conn.autocommit = True
        cursor = self.dbx.conn.cursor()
        cursor.execute(query, (self.file_id,self.processor_id,))
        # Close the cursor and connection
        cursor.close()        
        self.dbx.conn.commit()    

        self.update_table_attribute('trans_withdraw_date',self.withdrawal_date)
        # self.update_table_attribute('trans_withdraw_desc',trim_last_character(self.withdrawal_description,"| "))
        self.update_table_attribute('trans_withdraw_amt',self.withdrawal_amt)
        self.update_table_attribute('trans_deposit_date',self.deposit_date)
        # self.update_table_attribute('trans_deposit_desc',trim_last_character(self.deposit_description,"| "))        
        self.update_table_attribute('trans_deposit_amt',self.deposit_amt)
        # self.update_table_attribute('table_item',self.withdrawal_date)


