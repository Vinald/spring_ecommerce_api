import os


class Audio:
    def __init__(self, audio_path):
        self.audio_path = audio_path

    def format_audio_path(self):
        if os.path.exists(self.audio_path):
            if self.audio_path[-1] == '/':
                self.audio_path = self.audio_path.strip()[:-1]
                return self.audio_path
            if self.audio_path[-1] != '/':
                return self.audio_path
        else:
            return None

    def gen_audio_path(self, audio_link):
        audio_path = self.format_audio_path()
        if audio_path is not None:
            if '/en/' in audio_link:
                file = str(audio_link).split("audio/en/")[-1]
                path = (audio_path + '/en/' + str(file[:-4]))
                return path
            if '/lg/' in audio_link:
                file = str(audio_link).split("audio/lg/")[-1]
                path = (audio_path + '/lg/' + str(file[:-4]))
                return path
            if '/ly/' in audio_link:
                file = str(audio_link).split("audio/ly/")[-1]
                path = (audio_path + '/ly/' + str(file[:-4]))
                return path
        else:
            return audio_link

