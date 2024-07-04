
from fastapi import FastAPI
from typing import Any, Literal, Union
from fastapi import Depends, FastAPI, Body, HTTPException, Header, Request, Security
from fastapi.security import api_key

from sdapi import StableDiffusionInstance, StableDiffusionDistributor, SDTxt2ImgParams, Operation, OperationStatus

import uvicorn
import time

APP_API_KEY : str = None

async def set_api_key( value : str ) -> None:
	global APP_API_KEY
	APP_API_KEY = value

async def validate_api_key(
	key : Union[str, None] = Security(api_key.APIKeyHeader(name="X-API-KEY"))
) -> None:
	if APP_API_KEY is not None and key != APP_API_KEY:
		raise HTTPException(status_code=401, detail="Unauthorized")
	return None

async def host_fastapp(
	app : FastAPI,
	host : str,
	port : int
) -> None:
	print(f"Hosting App: {app.title}")
	await uvicorn.Server(uvicorn.Config(app, host=host, port=port, log_level='debug')).serve()

sdapi_hook_v2 = FastAPI(title='Stable Diffusion Hook V2', summary='Hooking onto Stable Diffusion WebUI for Roblox', version='0.1.0')

@sdapi_hook_v2.middleware("http")
async def process_time_adder( request : Request, call_next ) -> Any:
	start_time = time.time()
	response = await call_next(request)
	process_time = time.time() - start_time
	response.headers["X-Process-Time"] = str(process_time)
	return response

@sdapi_hook_v2.get('/')
async def root() -> str:
	return "OK"

@sdapi_hook_v2.get('/temp', dependencies=[Depends(validate_api_key)])
async def temp() -> bool:
	return True

async def main( host : str = '0.0.0.0', port : int = 5100, api_key : str = None ) -> None:
	print(f'Setting API_Key to "{api_key}"')
	await set_api_key(api_key)
	await host_fastapp(sdapi_hook_v2, host, port)
