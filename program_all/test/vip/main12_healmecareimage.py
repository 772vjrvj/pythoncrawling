import os
import csv
from datetime import datetime

def collect_image_data(base_dir, url_prefix, shop_prefix, start_index):
    data = []
    image_index = start_index
    create_dt = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    for shop_id in os.listdir(base_dir):
        shop_path = os.path.join(base_dir, shop_id)
        if not os.path.isdir(shop_path):
            continue

        for filename in os.listdir(shop_path):
            if not filename.lower().endswith(('.jpg', '.jpeg', '.png', '.gif')):
                continue

            image_id = f'IMG20250720205514{str(image_index).zfill(5)}'
            file_path = f'{url_prefix}{shop_id}/{filename}'
            data.append({
                'image_id': image_id,
                'file_path': file_path,
                'file_name': filename,
                'origin_name': filename,
                'delete_yn': 'N',
                'create_dt': create_dt,
                'shop_id': f'{shop_prefix}{shop_id}'
            })
            image_index += 1

    return data, image_index

# 경로 설정
vip_base = os.path.join('images', 'vip')
ya_base = os.path.join('images', '1004ya')

# 데이터 수집
vip_data, next_index = collect_image_data(
    base_dir=vip_base,
    url_prefix='https://healmecare.com/uploads/img/detail/v/',
    shop_prefix='V_',
    start_index=1
)

ya_data, _ = collect_image_data(
    base_dir=ya_base,
    url_prefix='https://healmecare.com/uploads/img/detail/n/',
    shop_prefix='N_',
    start_index=next_index
)

# CSV로 저장
all_data = vip_data + ya_data
with open('image_mapping.csv', 'w', newline='', encoding='utf-8-sig') as f:
    writer = csv.DictWriter(f, fieldnames=[
        'image_id', 'file_path', 'file_name', 'origin_name',
        'delete_yn', 'create_dt', 'shop_id'
    ])
    writer.writeheader()
    writer.writerows(all_data)
