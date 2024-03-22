import json
from datetime import datetime,timedelta
import base64
from db_connection import db_connection_manage
import sys
import os


conct = db_connection_manage()

class Categories():
    def create_category(request_body):
        try:
            data = request_body
            env_type = data['env_type']
            db_conct = conct.get_conn(env_type)
            db_con = db_conct['db']
            client = db_conct['client']
            sk_timeStamp=(datetime.now()+ timedelta(hours=5,minutes=30)).isoformat()
            categoryName = data['categoryName'].strip()
            basic_categories = ["Crystals","Mosfet","Inductor","Switch","Resistor","Transistor","Ferrite Bead","Diode","Led","Fuse","Ic","Connector","Capacitor"]
            lsi_key = "Static" if categoryName in basic_categories else "Dynamic"
            image_type=data['image_type']
            img=data['category_image']
            attr_list = [value.strip().lower() for value in data['product_attributes'].values()]
            subcat_list = [value.strip().lower() for value in data['sub_categories'].values()]
            if len(data['product_attributes'])==0:
                return{"statusCode" : 404, "body" : "No attributes added"}
            if (len(attr_list)>len(set(attr_list))):
                return {"statusCode" : 409, "body" : "Duplicate Attributes cannot be created"}
            if data['ct_type']=='Electronic':
                if len(data['sub_categories'])==0:
                    return {"statusCode" : 404, "body" : "No sub categories added"}
                if (len(subcat_list)>len(set(subcat_list))):
                    return {"statusCode" : 409, "body" : "Duplicate Sub_categories cannot be created"}
            ctgr_details = {key:data['product_attributes'][key] for inx,key in enumerate(data['product_attributes'].keys())}
            sub_categories = {key:data['sub_categories'][key] for inx,key in enumerate(data['sub_categories'].keys())} if data['ct_type'] == 'Electronic' else ""
            categories = list(db_con.Categories.find({}))
            metadata = list(db_con.Metadata.find({}))
            if any(dictionary['ctgr_details']['ctgr_name'].lower() == categoryName.lower() and dictionary['department'] == data['ct_type'] for dictionary in categories):
                return {"statusCode" : 404, "body" : "Category name already exists"}
            category_id = "00001"
            metadataId = "00001"
            if categories:
                category_ids = [i["ctgr_details"]["ctgr_id"].replace("CTID_","") for i in categories]
                category_ids.sort(reverse=True)
                category_id=str(((5-len(str(int(category_ids[0])+1))))*"0")+str(int(category_ids[0])+1)
            if metadata:
                metadataIds = [i["mtdt_id"].replace("MDID_","") for i in metadata]
                metadataIds.sort(reverse=True)
                metadataId=str(((5-len(str(int(metadataIds[0])+1))))*"0")+str(int(metadataIds[0])+1)
            category_id = max(metadataId,category_id)
            upload_image = ''
            if img:
                image_64_decode = base64.b64decode(img)
                image_result = open(f"../../../cms-images/category/{data['ct_type']}/{category_id}/image.{image_type}", 'wb')
                image_result.write(image_64_decode)
                upload_image = f"../../../cms-images/category/{data['ct_type']}/{category_id}/image.{image_type}"
            categoryDetails={}
            categoryDetails['ctgr_id']="CTID_"+category_id
            categoryDetails['mtdt_id']="MDID_"+category_id
            categoryDetails["ctgr_image"] = upload_image
            categoryDetails["time_stamp"] = sk_timeStamp
            categoryDetails["ctgr_name"] = categoryName
            category_data = {
                "ct_id":"CTID_"+category_id,
                "timestamp": sk_timeStamp,
                "ctgr_details":categoryDetails,
                "department" : data['ct_type']
                }
            category_metadata= {
                    "mtdt_id" : "MDID_"+category_id,
                    "timestamp": str(sk_timeStamp),
                    "category_attributes" : ctgr_details,
                    "ctgr_name" : categoryName,
                    "lsi_key" : lsi_key,
                    "department":data['ct_type']
                }
            if data['ct_type'] == 'Electronic' and sub_categories:
                category_metadata['sub_categories'] = sub_categories
            db_con.Categories.insert_one(category_data)
            db_con.Metadata.insert_one(category_metadata)
            conct.close_connection(client)
            return {'statusCode': 200, 'body': f'New category {categoryName} created successfully'}
        except Exception as err:
            exc_type, exc_obj, tb = sys.exc_info()
            f_name = tb.tb_frame.f_code.co_filename
            line_no = tb.tb_lineno
            print(f"Error {exc_type.__name__} in file {f_name}, line {line_no}: {err}")
            return {'statusCode': 400,'body': 'Internal server error'}
        
    def delete_category(request_body):
        try:
            data = request_body
            env_type = data['env_type']
            db_conct = conct.get_conn(env_type)
            db_con = db_conct['db']
            client = db_conct['client']
            category = data['ctgr_id']
            ct_type=data['type']
            category_data = list(db_con.Categories.find_one({"ctgr_details.ctgr_id": category}))
            category_metaData = list(db_con.Metadata.find_one({"mtdt_id": category.replace("CTID","MDID")}))
            category_inventory = list(db_con.Inventory.find_one({"component_details.ctgr_id":category}))
            if (len(category_metaData) and category_metaData[0]['lsi_key']=="Static"):
                conct.close_connection(client)
                return {'statusCode': 404, 'body': 'You cannot delete this category '}
            if len(category_inventory):
                conct.close_connection(client)
                return {'statusCode': 404, 'body': 'This Category cannot be deleted with components'}
            if category_metaData and category_data:
                filename = category_data[0]['ctgr_details']["ctgr_image"]  
                db_con.categories.delete_one({"ctgr_details.ctgr_id": "CTID_0002"})
                db_con.Metadata.delete_one({"mtdt_id": category.replace("CTID","MDID")})
                if filename:
                    os.remove(filename)

                response = {'statusCode': 200, 'body': "Category Deleted Successfully"}
            else:
                response = {'statusCode': 400, 'body': "metadata or category data not found"}
            conct.close_connection(client)
            return response
        except Exception as err:
            exc_type, exc_obj, tb = sys.exc_info()
            f_name = tb.tb_frame.f_code.co_filename
            line_no = tb.tb_lineno
            print(f"Error {exc_type.__name__} in file {f_name}, line {line_no}: {err}")
            return {'statusCode': 400,'body': 'Category deletion failed'}
    
    def edit_category(request_body):
        try:
            data = request_body
            env_type = data['env_type']
            db_conct = conct.get_conn(env_type)
            db_con = db_conct['db']
            client = db_conct['client']
            if data["dep_type"]=="Electronic":
                if data["sub_categories"] :
                    new_category_name =  data['ctgr_name']
                    attr_list = [value.strip().lower() for value in data['product_attributes'].values()]
                    subcat_list = [value.strip().lower() for value in data['sub_categories'].values()]
                    if len(data['product_attributes'])==0:
                        conct.close_connection(client)
                        return {"statusCode" : 404, "body" : "No attributes added"}
                    if (len(attr_list)>len(set(attr_list))):
                        conct.close_connection(client)
                        return {"statusCode" : 409, "body" : "Duplicate Attributes cannot be created"}
                    if data['dep_type']=='Electronic':
                        if len(data['sub_categories'])==0:
                            conct.close_connection(client)
                            return {"statusCode" : 404, "body" : "No sub categories added"}
                        if (len(subcat_list)>len(set(subcat_list))):
                            conct.close_connection(client)
                            return {"statusCode" : 409, "body" : "Duplicate Sub_categories cannot be created"}
                    ctgry_lst = list(db_con.Categories.find({}))
                    categoryId = data['ctgr_id']
                    ctgr_name_lst=[i["ctgr_details"]["ctgr_name"].lower() for i in ctgry_lst if i["ctgr_details"]["ctgr_id"]!=data['ctgr_id'] and i["department"]==data['dep_type']]
                    if data["new_category"].lower().strip() in ctgr_name_lst:
                        conct.close_connection(client)
                        return{"statusCode" : 404, "body" : "Category name already exists"}
                    _subcategories = data['sub_categories'].keys()
                    inventory = list(db_con.Inventory.find({}))
                    if any(1 for item in inventory if item['ctgr_details']['sub_ctgr'] not in _subcategories):
                        conct.close_connection(client)
                        return {"statusCode" : 404, "body" : "You cannot delete a subcategory for which inventory is present"}
                    metadataId = ctgry[0]["ctgr_details"]["mtdt_id"]
                    metadata = list(db_con.Metadata.find({"mtdt_id":metadataId}))
                    result = db_con.Categories.update_one(
                            {"ctgr_details.ctgr_id": categoryId},  # filter
                            {"$set": {"ctgr_details.ctgr_name": new_category_name}}  # update
                        )
                    result = db_con.Metadata.update_one(
                            {"mtdt_id": categoryId.replace("CTID","MDID")},  # filter
                            {"$set": {"category_attributes": {key:value.strip() for key,value in data["product_attributes"].items()},
                                      "sub_categories":{key:value.strip() for key,value in data["sub_categories"].items()},
                                      "ctgr_name":new_category_name
                                }
                            }
                        )
                    conct.close_connection(client)
                    return {"statusCode": 200, "body": "Electric category details changed successfully"}
                else:
                    conct.close_connection(client)
                    return {'statusCode': 404,'body': 'Please add SubCategory'}
            elif data["dep_type"]=="Mechanic":
                print(data)
                attr_list = [value.strip().lower() for value in data['product_attributes'].values()]
                if len(data['product_attributes'])==0:
                    conct.close_connection(client)
                    return {"statusCode" : 404, "body" : "No attributes added"}
                if (len(attr_list)>len(set(attr_list))):
                    conct.close_connection(client)
                    return {"statusCode" : 404, "body" : "Duplicate Attributes cannot be created"}
                new_category_name =  data['ctgr_name']
                ctgry_lst = list(db_con.Categories.find({}))
                ctgr_name_lst=[i["ctgr_details"]["ctgr_name"].lower().strip() for i in ctgry_lst if i["ctgr_details"]["ctgr_id"]!=data['ctgr_id'] and i["department"]==data['dep_type']]
                if  data["new_category"].lower().strip() in ctgr_name_lst:
                    conct.close_connection(client)
                    return{"statusCode" : 404, "body" : "Category name already exists"}
                categoryId = data['ctgr_id']
                ctgry = [ctgr for ctgr in ctgry_lst if ctgr['ct_id']==categoryId]
                metadataId = ctgry[0]["ctgr_details"]["mtdt_id"]
                metadataId = ctgry[0]["ctgr_details"]["mtdt_id"]
                result = db_con.Categories.update_one(
                        {"ctgr_details.ctgr_id": categoryId},  # filter
                        {"$set": {"ctgr_details.ctgr_name": new_category_name}}  # update
                    )
                result = db_con.Metadata.update_one(
                    {
                        "mtdt_id": categoryId.replace("CTID","MDID")},  # filter
                        {
                            "$set": 
                                {
                                    "category_attributes": {key:value.strip() for key,value in data["product_attributes"].items()},
                                    "ctgr_name":new_category_name
                                }
                            }
                        )
                conct.close_connection(client)
                return {"statusCode": 200, "body": "Electric category details changed successfully"}
        except Exception as err:
            exc_type, exc_obj, tb = sys.exc_info()
            f_name = tb.tb_frame.f_code.co_filename
            line_no = tb.tb_lineno
            print(f"Error {exc_type.__name__} in file {f_name}, line {line_no}: {err}")
            return {'statusCode': 400,'body': 'Internal server error'}
    
    def get_category(request_body):
        try:
            data = request_body
            env_type = data['env_type']
            db_conct = conct.get_conn(env_type)
            db_con = db_conct['db']
            client = db_conct['client']
            category = data['ctgr_name']
            ctgr_id=data['ctgr_id']
            category_info = list(db_con.Categories.find({"ctgr_details.ctgr_name":category,"ctgr_details.ctgr_id":ctgr_id}))
            if category_info:
                category_info = category_info[0]
                metadataId = category_info['ctgr_details']['mtdt_id']
                metadata_info = db_con.Metadata.find({"mtdt_id":metadataId})
                category_data = {}
                if metadata_info:
                    result = metadata_info[0]
                    category_data['ctgr_name'] = category
                    category_data['product_attributes'] = result['category_attributes']  
                    category_data['department']=result['gsipk_id']
                    if category_info['gsipk_id'] == 'Electronic':
                        category_data['sub_categories'] = result['sub_categories']
                        category_data['department']=result['gsipk_id']
                    category_data["new_category"]=category
                    conct.close_connection(client)
                    return {'statusCode': 200, 'body': category_data}
                conct.close_connection(client)
                return {'statusCode': 404, 'body': 'No data found in Metadata'}
            else:
                conct.close_connection(client)
                return {"statusCode": 404, "body": "category data is no there"}
        except Exception as err:
            exc_type, exc_obj, tb = sys.exc_info()
            f_name = tb.tb_frame.f_code.co_filename
            line_no = tb.tb_lineno
            print(f"Error {exc_type.__name__} in file {f_name}, line {line_no}: {err}")
            return {'statusCode': 400,'body': 'There is an AWS Lambda Data Capturing Error'}
    
    def get_all_categories_for_department(request_body):
        try:
            data = request_body
            env_type = data['env_type']
            db_conct = conct.get_conn(env_type)
            db_con = db_conct['db']
            client = db_conct['client']
            department = data['ct_type']
            db = list(db_con.Categories.find({}))
            lst = []
            db = [i["ctgr_details"] for i in db]
            for item in db:
                category_data = item
                dic = {}
                for k, v in item.items():
                    if isinstance(v, dict):
                        dic[k] = v
                    else:
                        dic[k] = v
                lst.append(dic)
                lst = sorted(lst, key=lambda x: x['ctgr_name'], reverse=False)
            print(lst)
            conct.close_connection(client)
            return {'statusCode': 200, 'body': lst}
        except Exception as err:
            exc_type, exc_obj, tb = sys.exc_info()
            f_name = tb.tb_frame.f_code.co_filename
            line_no = tb.tb_linenoo
            print(f"Error {exc_type.__name__} in file {f_name}, line {line_no}: {err}")
            return {'statusCode': 400,'body': []}