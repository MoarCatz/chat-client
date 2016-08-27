import time
from hashlib import sha256

code = input()
st = str(time.time()).replace('.', '') + code

sha = sha256(st.encode())
print(sha.hexdigest())
