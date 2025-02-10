import hashlib

plaintext = "ecd71870d1963316a97e3ac3408c9835ad8cf0f3c1bc703527c30265534f75ae"
hash_value = hashlib.sha256(plaintext.encode()).hexdigest()
print(hash_value)