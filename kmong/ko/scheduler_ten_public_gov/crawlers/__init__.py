from .kistep_gps_trend import KistepGpsTrend
from .kistep_board import KistepBoard
from .krei_list import KreiList
from .krei_research import KreiResearch
from .kati_export import KatiExport
from .kati_report import KatiReport
from .stepi_report import StepiReport
from .moa_press import MoaPress
from .maff_press import MaffPress
from .usda_press import UsdaPress

# 객체들을 미리 생성하여 저장
crawler_instances = {
    'KistepGpsTrend': KistepGpsTrend(),
    'KistepBoard': KistepBoard(),
    'KreiList': KreiList(),
    'KreiResearch': KreiResearch(),
    'KatiExport': KatiExport(),
    'KatiReport': KatiReport(),
    'StepiReport': StepiReport(),
    'UsdaPress': UsdaPress(),
    'MaffPress': MaffPress(),
    'MoaPress': MoaPress(),
}

crawler_list = [
    'KistepGpsTrend',
    'KistepBoard',
    'KreiList',
    'KreiResearch',
    'KatiExport',
    'KatiReport',
    'StepiReport',
    'UsdaPress',
    'MaffPress',
    'MoaPress'
]

def get_crawler(class_name):
    """클래스 이름에 맞는 크롤러 객체를 리턴"""
    return crawler_instances.get(class_name)