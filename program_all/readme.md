2025-06-08

Python 3.13.4
pip 25.1.1

pip install -r requirements.txt


pyinstaller main.py `
  --icon "./image/crawling.ico" `
--name main `
  --noconsole `
--distpath "./dist" `
  --workpath "./build" `
--hidden-import sip `
  --hidden-import numpy `
--collect-all numpy `
  --collect-all pandas `
--add-data "resources;resources"


2025-08-09
abc_program_v9


https://mullvad.net/ko
계정번호 : 5591478657770516



VSVersionInfo(
ffi=FixedFileInfo(
filevers=(1, 0, 0, 0),
prodvers=(1, 0, 0, 0),
mask=0x3f,
flags=0x0,
OS=0x4,
fileType=0x1,
subtype=0x0,
date=(0, 0)
),
kids=[
StringFileInfo([
StringTable(
'040904B0',
[
StringStruct('CompanyName', 'PANDO'),
StringStruct('FileDescription', 'GPM'),
StringStruct('FileVersion', '1.0.0.0'),
StringStruct('InternalName', 'main'),
StringStruct('OriginalFilename', 'main.exe'),
StringStruct('ProductName', 'PANDO'),
StringStruct('ProductVersion', '1.0.0.0'),
]
)
]),
VarFileInfo([VarStruct('Translation', [1033, 1200])])
]
)

