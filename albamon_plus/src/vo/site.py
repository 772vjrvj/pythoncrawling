class Site:
    def __init__(self, label, key, color, enabled=True):
        self.label = label
        self.key = key
        self.color = color
        self.enabled = enabled

    def is_enabled(self):
        return self.enabled