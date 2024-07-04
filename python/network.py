
from typing import Any, Literal, Union
from pydantic import BaseModel, Field
from fastapi import FastAPI
from fastapi import Depends, FastAPI, Body, HTTPException, Header, Request, Security
from fastapi.security import api_key

from sdapi import StableDiffusionInstance, StableDiffusionDistributor, SDTxt2ImgParams, Operation, OperationStatus, ASPECT_RATIO_MAP, load_bs4_image, timestamp

import uvicorn
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

class RobloxParameters(BaseModel):
	player_name : str = Field(None)
	user_id : int = Field(None)
	timestamp : int = Field(default_factory=timestamp)

	checkpoint : str = Field(None)

	prompt : str = Field(None)
	negative : str = Field(None)

	steps : int = Field(25)
	cfg_scale : float = Field(7.0)
	sampler_name : str = Field('Eular a')

	size : str = Field("512x512")
	seed : int = Field(-1)

def log_roblox_params( params : RobloxParameters ) -> None:
	print(params.model_dump_json())

async def queue_roblox_txt2img( distributor : StableDiffusionDistributor, params : RobloxParameters ) -> tuple[bool, str]:
	if params.player_name is not None and params.user_id is not None:
		log_roblox_params(params)

	if params.size not in ASPECT_RATIO_MAP.keys():
		return False, 'Invalid size parameter - must be an aspect ratio mapped value.'

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

	return await distributor.queue_txt2img(params)

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
