import os


class Audio:
    def __init__(self, path):
        self.path = path

    def get_audio_path(self):
        if not os.path.exists(self.path):
            return None
        if self.path[-1] == '/':
            return self.path.strip()[:-1]
        return self.path

    def gen_audio_file(self, link):
        path = self.get_audio_path() + link
        if not os.path.exists(path):
            return link
        return os.path.splitext(path)[0]
