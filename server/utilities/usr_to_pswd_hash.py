# This is not part of the actual server

from hashlib import sha256
password = (input() + '2016')[::-1] + 'mysalt'
sha = sha256(password.encode())
print(sha.hexdigest())
