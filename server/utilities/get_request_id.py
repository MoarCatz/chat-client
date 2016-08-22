import time
from hashlib import md5

code = input()
st = str(time.time()).replace('.', '') + code

md = md5(st.encode())
print(md.hexdigest())

