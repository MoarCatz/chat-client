# This is not part of the actual server

from hashlib import md5
password = (input() + '2016')[::-1] + 'mysalt'
md = md5(password.encode())
print(md.hexdigest())
