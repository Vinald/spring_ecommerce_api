import hashlib


class Hash:
    @staticmethod
    def hash(string: str):
        return hashlib.md5(string.encode()).hexdigest()
