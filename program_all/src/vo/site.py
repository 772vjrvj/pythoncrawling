# src/vo/site.py
class Site:
    def __init__(self, label=None, key=None, color=None, enabled=True, setting=None, setting_detail=None, columns=None, region=None, popup=False, sites=False):
        self.label = label
        self.key = key
        self.color = color
        self.enabled = enabled
        self.setting = setting
        self.setting_detail = setting_detail
        self.columns = columns
        self.region = region
        self.popup = popup
        self.sites = sites

    def is_enabled(self):
        return self.enabled