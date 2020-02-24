import os


class Audio:
    def __init__(self, audio_path):
        self.audio_path = audio_path

    def get_audio_path(self):
        if not os.path.exists(self.audio_path):
            return None
        if self.audio_path[-1] == '/':
            return self.audio_path.strip()[:-1]
        return self.audio_path

    def gen_audio_file(self, link):
        audio_path = self.get_audio_path()
        audio_file_name = link.split('audio')[-1]
        audio_path = audio_path + audio_file_name
        if not os.path.exists(audio_path):
            return link
        return os.path.splitext(audio_path)[0]
