
from __future__ import annotations
from typing import Any, Literal, Union
from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel, Field
from fastapi import FastAPI
from fastapi import Depends, FastAPI, Body, HTTPException, Header, Request, Security
from fastapi.security import api_key
from pyngrok import ngrok
from threading import Thread

from sdapi import SDTxt2ImgParams, StableDiffusionInstance, StableDiffusionDistributor, SDImage, Operation, OperationStatus, load_bs4_image, timestamp

import json
import uvicorn
import zlib
import rsa
import time

ASPECT_RATIO_MAP : dict[str, tuple[int, int]] = {
	"512x512" : (512, 512),
	"512x768" : (512, 768),
	"512x1024" : (512, 1024),
	"768x512" : (768, 512),
	"768x768" : (768, 768),
	"768x1024" : (768, 1024),
	"1024x512" : (1024, 512),
	"1024x768" : (1024, 768),
	"1024x1024" : (1024, 1024),
}

def log_roblox_params( params : RobloxParameters ) -> None:
	print(params.model_dump_json())

class RobloxUser(BaseModel):
	user_id : int = Field(None)
	player_name : str = Field(None)

class RobloxParameters(BaseModel):
	roblox_user : RobloxUser = Field(None)
	timestamp : int = Field(default_factory=timestamp)

	checkpoint : str = Field(None)

	prompt : str = Field(None)
	negative : str = Field(None)

	steps : int = Field(25)
	cfg_scale : float = Field(7.0)
	sampler_name : str = Field('Euler a')

	size : str = Field("512x512")
	seed : int = Field(-1)

LOCAL_DISTRIBUTOR = StableDiffusionDistributor([StableDiffusionInstance('http://127.0.0.1:7860')])
APP_API_KEY : str = None

async def set_api_key( value : Union[str, None] ) -> None:
	global APP_API_KEY
	APP_API_KEY = value

async def validate_api_key(key : Union[str, None] = Security(api_key.APIKeyHeader(name="X-API-KEY", auto_error=False))) -> None:
	if APP_API_KEY is not None and key != APP_API_KEY:
		raise HTTPException(status_code=401, detail="Unauthorized")
	return None

async def host_fastapp(app : FastAPI, host : str, port : int) -> None:
	print(f"Hosting App: {app.title}")
	await uvicorn.Server(uvicorn.Config(app, host=host, port=port, log_level='debug')).serve()

sdapi_hook_v2 = FastAPI(title='Stable Diffusion Hook V2', summary='Hooking onto Stable Diffusion WebUI for Roblox', version='0.1.0')

client_rsa : dict = {} # public keys for server to use to communicate with client
server_rsa : dict = {} # public key for clients to use, private keys to decrypt with

# TODO: implement properly
# async def rsa_decrypt_pass(request : Request) -> None:
# 	'''decrypt messages being received by clients'''
# 	# find keypair with identifier
# 	identifier : str = request.headers.get('X-RSA-MARKER')
# 	print(identifier)
# 	rsa_keypair : tuple[rsa.PublicKey, rsa.PrivateKey] = None if identifier is None else server_rsa.get(identifier)
# 	if rsa_keypair is None: return # no identifier match
# 	# decrypt with private key
# 	print(str(rsa_keypair[0]))
# 	body = await request.body()
# 	if len(body.decode('utf-8')) == 0: return # no body to decrypt
# 	print(body)
# 	request._body = rsa.decrypt( bytes.fromhex(body.decode('utf-8')), rsa_keypair[1] )

# TODO: implement properly
# async def rsa_encrypt_pass(request : Request, response : Any) -> Union[Any, str]:
# 	'''sending messages back to client rsa encrypted'''
# 	# find public key with identifier
# 	identifier : str = request.headers.get('X-RSA-MARKER')
# 	print(identifier)
# 	rsa_public : rsa.PublicKey = None if identifier is None else client_rsa.get(identifier)
# 	if rsa_public is None: return response
# 	# encrypt it for the client to receive
# 	print(type(response), response)
# 	eresponse : str = json.dumps(jsonable_encoder(response))
# 	eresponse : str = rsa.encrypt(response, rsa_public).hex()
# 	return eresponse

# TODO: implement properly
# @sdapi_hook_v2.middleware("http")
# async def encryption_process(request: Request, call_next):
# 	await rsa_decrypt_pass(request)
# 	response : Any = await call_next(request)
# 	return await rsa_encrypt_pass(request, response)

@sdapi_hook_v2.get('/')
async def root() -> str:
	return "OK"

@sdapi_hook_v2.post('/setup_rsa')
async def setup_rsa( identifier : str = Body(None, embed=True), public_key : str = Body(None, embed=True) ) -> Union[str, None]:
	if identifier in server_rsa.keys():
		return None
	public, private = rsa.newkeys(1024)
	n, e = public_key.split(',')
	client_rsa[identifier] = rsa.PublicKey(n=int(n[1:]), e=int(e[:-1])) # for server to use
	server_rsa[identifier] = (public, private) # for clients to use
	return f'{public.n},{public.e}'

@sdapi_hook_v2.post('/get_public_key')
async def get_public_key( identifier : str = Body(None, embed=True) ) -> Union[str, None]:
	if identifier in server_rsa.keys():
		public : rsa.PublicKey = server_rsa[identifier][0]
		return f'{public.n},{public.e}'
	return None

@sdapi_hook_v2.get('/total_instances', dependencies=[Depends(validate_api_key)])
async def total_instances() -> int:
	return len(LOCAL_DISTRIBUTOR.instances)

@sdapi_hook_v2.get('/queue_length', dependencies=[Depends(validate_api_key)])
async def queue_length() -> int:
	return len(LOCAL_DISTRIBUTOR.queue)

@sdapi_hook_v2.get('/total_operations', dependencies=[Depends(validate_api_key)])
async def total_operations() -> int:
	return len(LOCAL_DISTRIBUTOR.operations.keys())

@sdapi_hook_v2.get('/get_instance_infos', dependencies=[Depends(validate_api_key)])
async def get_instance_infos() -> list[dict]:
	return await LOCAL_DISTRIBUTOR.get_instances_infos()

@sdapi_hook_v2.post('/get_operation_status', dependencies=[Depends(validate_api_key)])
async def get_operation_status( operation_id : str = Body(embed=True) ) -> int:
	return await LOCAL_DISTRIBUTOR.get_operation_status(operation_id)

@sdapi_hook_v2.post('/is_operation_completed', dependencies=[Depends(validate_api_key)])
async def is_operation_completed( operation_id : str = Body(embed=True) ) -> bool:
	return await LOCAL_DISTRIBUTOR.is_operation_completed(operation_id)

@sdapi_hook_v2.post('/get_operation_metadata', dependencies=[Depends(validate_api_key)])
async def get_operation_metadata( operation_id : str = Body(embed=True) ) -> dict:
	operation : Operation = LOCAL_DISTRIBUTOR.operations.get(operation_id)
	if operation is None:
		return None
	return {"state" : operation.state, "timestamp" : operation.timestamp, "error" : operation.error}

@sdapi_hook_v2.post('/get_operation_progress', dependencies=[Depends(validate_api_key)])
async def get_operation_progress( operation_id : str = Body(embed=True) ) -> dict:
	return await LOCAL_DISTRIBUTOR.get_operation_progress(operation_id)

@sdapi_hook_v2.post('/cancel_operation', dependencies=[Depends(validate_api_key)])
async def cancel_operation( operation_id : str = Body(embed=True) ) -> None:
	await LOCAL_DISTRIBUTOR.cancel_operation(operation_id)
	return None

# TODO: implement properly
@sdapi_hook_v2.post('/get_operation_images', dependencies=[Depends(validate_api_key)])
async def get_operation_images( operation_id : str = Body(embed=True) ) -> list[dict]:
	images : list[SDImage] = await LOCAL_DISTRIBUTOR.get_operation_images(operation_id)
	if images is None:
		return None
	return [{'size' : item.size, 'image' : len(zlib.compress(item.data.encode('utf-8')))} for item in images]

@sdapi_hook_v2.post('/queue_txt2img', dependencies=[Depends(validate_api_key)])
async def queue_txt2img( params : RobloxParameters = Body(embed=True) ) -> str:
	if params.roblox_user is not None:
		log_roblox_params(params)

	if params.size not in ASPECT_RATIO_MAP.keys():
		return False, 'Invalid size parameter - must be an aspect ratio mapped value.'

	if params.steps < 1 or params.steps > 30:
		return False, 'Invalid steps parameter - must be between 1 and 30.'

	width, height = ASPECT_RATIO_MAP.get(params.size)

	print(f'Queueing Roblox txt2img parameters: {params.model_dump_json(indent=None)}')

	params = SDTxt2ImgParams(
		checkpoint=params.checkpoint,
		prompt=params.prompt,
		negative=params.negative,
		steps=params.steps,
		cfg_scale=params.cfg_scale,
		sampler_name=params.sampler_name,
		width=width,
		height=height,
		seed=params.seed,
	)

	return await LOCAL_DISTRIBUTOR.queue_txt2img(params)

class Ngrok:
	'''Ngrok singleton class - manages the ngrok tunnel - old code xd'''
	port = 8080
	tunnel = None
	_thread = None

	@staticmethod
	def _internal_start_tunnel(port : int) -> None:
		'''
		Connect to the ngrok servers with the given port.
		'''
		Ngrok.tunnel = ngrok.connect(port)

	@staticmethod
	def set_port(port : int) -> None:
		'''
		Set the port.
		'''
		Ngrok.port = port

	@staticmethod
	def open_tunnel() -> None:
		'''
		Open the ngrok tunnel if it is not open already.
		'''
		assert Ngrok.tunnel is None, "Tunnel is already open (tunnel reference)."
		assert Ngrok._thread is None, "Tunnel is already open (thread exists)."
		Ngrok._thread = Thread(target=Ngrok._internal_start_tunnel, args=(Ngrok.port,), daemon=True)
		Ngrok._thread.start()
		if Ngrok.tunnel is None:
			print("Awaiting ngrok tunnel to start.")
			while Ngrok.tunnel is None:
				time.sleep(1)
		print("ngrok tunnel has started.")

	@staticmethod
	def close_tunnel() -> None:
		'''
		Close the ngrok tunnel if it is open.
		'''
		assert Ngrok.tunnel is not None, "Tunnel is non-existent."
		Ngrok._thread = None
		ngrok.disconnect( Ngrok.get_ngrok_addr() )
		Ngrok.tunnel = None

	@staticmethod
	def get_ngrok_addr() -> str:
		'''
		Get the ngrok address for web requests.
		'''
		assert Ngrok.tunnel is not None, "You must open the tunnel before you can get the address."
		return Ngrok.tunnel.public_url

	@staticmethod
	def await_ngrok_addr() -> str:
		while Ngrok.tunnel is None:
			time.sleep( 0.25 )
		return Ngrok.tunnel.public_url

async def localhost( host : str = '0.0.0.0', port : int = 5100, api_key : str = None ) -> None:
	print(f'Setting API_Key to "{api_key}"')
	await LOCAL_DISTRIBUTOR.initialize()
	_ = await LOCAL_DISTRIBUTOR.find_unavailable_instances()
	await set_api_key(api_key)
	await host_fastapp(sdapi_hook_v2, host, port)
	await LOCAL_DISTRIBUTOR.shutdown()
