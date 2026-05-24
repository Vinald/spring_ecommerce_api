import hashlib


class Hash:
    @staticmethod
    def hash(string: str):
        # CHANGED: was hashlib.md5 — MD5 is cryptographically broken and unsuitable
        # for generating security-sensitive IDs. SHA-256 is collision-resistant.
        return hashlib.sha256(string.encode()).hexdigest()
