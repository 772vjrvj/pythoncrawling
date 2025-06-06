class Site:
    def __init__(self, label, key, color, enabled=True, user=False):
        self.label = label
        self.key = key
        self.color = color
        self.enabled = enabled
        self.user = user

    def is_enabled(self):
        return self.enabled