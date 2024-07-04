
# from typing import Union, Any
# from uuid import uuid4

# import json
# import rsa
# import requests

# # generate new identifier
# unique_client : str = uuid4().hex
# print(unique_client)

# # generate a new rsa pair
# client_public, client_private = rsa.newkeys(1024)
# print(str(client_public), str(client_private))

# # setup rsa with server and get server public key
# response = requests.post('http://127.0.0.1:5100/setup_rsa', json={'identifier' : unique_client, 'public_key' : f'{client_public.n},{client_public.e}'})
# print(response.text)
# n, e = response.text.split(',')
# server_public = rsa.PublicKey(n=int(n[1:]), e=int(e[:-1]))
# print(str(server_public))

# # test communication
# response = requests.post('http://127.0.0.1:5100/get_public_key', json={'identifier' : unique_client})
# print(response.text)

# # test rsa
# response = requests.get('http://127.0.0.1:5100/total_instances', headers={'X-RSA-MARKER' : unique_client})
# print(response.text)
# # print(rsa.decrypt(bytes.fromhex(response.text), client_private).decode('utf-8'))
