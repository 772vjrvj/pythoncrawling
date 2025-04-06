# 삭제 여기 시작
# obj_list = self.csv_appender.load_rows()
# delete_obj_list = []
# for index_dt, obj in enumerate(obj_list):
#     print(f'index_dt : {index_dt}')
#     if obj.get('website') != "ZARA":
#         continue

# if obj.get('imageUrl') == "" or obj.get('imageUrl') == None or obj.get('imageUrl') == 'https://static.zara.net/stdstatic/6.63.1/images/transparent-background.png' or obj.get('imageUrl') == 'https://static.zara.net/stdstatic/6.59.2/images/transparent-background.png' :
#     print(f'삭제할 놈 obj : {obj}')
#     delete_obj_list.append(obj)
# if obj.get('productKey') == "ZARA_435257838" or obj.get('productKey') == "ZARA_434455281":
#     print(f'삭제할 놈 obj : {obj}')
#     delete_obj_list.append(obj)

# for idxd, delete_obj in enumerate(delete_obj_list):
#     print(f'삭제시작 idx : {idxd}, delete_obj : {delete_obj}')
#     self.google_uploader.delete_image(delete_obj)
#     self.server_api.delete_product(delete_obj.get('productKey'))

# obj_list = self.csv_appender.load_rows()
# delete_obj_list = []
# for index_dt, obj in enumerate(obj_list):
#     print(f'index_dt : {index_dt}')
#     if obj.get('productKey') == 'ZARA_446575549':
#         print(f'삭제할 놈 obj : {obj}')
#         delete_obj_list.append(obj)
#
# for idxd, delete_obj in enumerate(delete_obj_list):
#     print(f'삭제시작 idx : {idxd}, delete_obj : {delete_obj}')
#     self.google_uploader.delete_image(delete_obj)
#     self.server_api.delete_product(delete_obj.get('productKey'))

# 삭제
# 여기 끝


# self.google_uploader.delete(obj)

# self.google_uploader.download_all_in_folder(obj)