import ssl
import socket
import hashlib
 

def get_thumbprint(fqdn):
  if not fqdn:
    raise ValueError
  sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
  sock.settimeout(1)
  wrappedSocket = ssl.wrap_socket(sock)
  try:
    wrappedSocket.connect((fqdn, 443))
  except:
    response = False
  else:
    der_cert_bin = wrappedSocket.getpeercert(True)
    thumb_sha256 = hashlib.sha256(der_cert_bin).hexdigest()
    wrappedSocket.close()
    return thumb_sha256
