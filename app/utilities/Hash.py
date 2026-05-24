import hashlib


class Hash:
    @staticmethod
    def hash(string: str):
        return hashlib.sha256(string.encode()).hexdigest()
