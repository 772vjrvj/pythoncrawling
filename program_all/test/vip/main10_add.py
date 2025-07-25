import pandas as pd
import re

def process_vip(file_path, output_path):
    df = pd.read_excel(file_path)

    # SHOP_NAME: "망포-테라피" 형식 처리
    def split_shop_name(name):
        try:
            parts = str(name).split('-', 1)
            loc = parts[0].strip() if len(parts) > 0 else ''
            nm = parts[1].strip() if len(parts) > 1 else ''
            return pd.Series([loc, nm, f"{loc}_{nm}"])
        except Exception:
            return pd.Series(['', '', ''])

    df[['SHOP_NAME_LOC', 'SHOP_NAME_NM', 'SHOP_NAME_REAL']] = df['SHOP_NAME'].apply(split_shop_name)
    df['SITE'] = 'vipinfo'

    df.to_excel(output_path, index=False)
    print(f"✅ VIP 파일 처리 완료 → {output_path}")


def process_nabiya(file_path, output_path):
    df = pd.read_excel(file_path)

    # SHOP_NAME: "안산.고잔[뉴테라피]" 형식 처리
    def extract_shop_parts(name):
        try:
            name = str(name)
            loc = name.split('.')[0].strip() if '.' in name else ''
            match = re.search(r'\[(.*?)\]', name)
            nm = match.group(1).strip() if match else ''
            return pd.Series([loc, nm, f"{loc}_{nm}"])
        except Exception:
            return pd.Series(['', '', ''])

    df[['SHOP_NAME_LOC', 'SHOP_NAME_NM', 'SHOPNAME_REAL']] = df['SHOP_NAME'].apply(extract_shop_parts)
    df['SITE'] = '나비야넷'

    df.to_excel(output_path, index=False)
    print(f"✅ 나비야넷 파일 처리 완료 → {output_path}")


# 파일 경로
vip_input = 'vip 최종.xlsx'
vip_output = 'vip 최종_추가됨.xlsx'

nabiya_input = '나비야넷 최종.xlsx'
nabiya_output = '나비야넷 최종_추가됨.xlsx'

# 실행
process_vip(vip_input, vip_output)
process_nabiya(nabiya_input, nabiya_output)
