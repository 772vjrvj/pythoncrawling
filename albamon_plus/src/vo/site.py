class Site:
    def __init__(self, label=None, key=None, color=None, enabled=True, user=False, setting=None):
        self.label = label
        self.key = key
        self.color = color
        self.enabled = enabled
        self.user = user
        self.setting = setting

    def is_enabled(self):
        return self.enabled