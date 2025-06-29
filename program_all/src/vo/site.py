class Site:
    def __init__(self, label=None, key=None, color=None, enabled=True, user=False, setting=None, columns=None, region=None):
        self.label = label
        self.key = key
        self.color = color
        self.enabled = enabled
        self.user = user
        self.setting = setting
        self.columns = columns
        self.region = region

    def is_enabled(self):
        return self.enabled