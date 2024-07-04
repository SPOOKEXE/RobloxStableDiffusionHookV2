
from uuid import uuid4
from pydantic import BaseModel, Field
from typing import Union
from enum import Enum

import json
import datetime
import asyncio
import aiohttp
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

def tztimestamp() -> str:
	return str(datetime.datetime.now(datetime.timezone.utc)).replace(' ', 'T', 1).replace('+00:00', 'Z')

def pop_indexes( value : dict, indexes : list[str] ) -> None:
	for index in indexes:
		if index in value:
			value.pop(index)

class APIEndpoints:
	'''Endpoints for the Stable Diffusion WebUI API'''
	sysinfo = '/internal/sysinfo'
	ping = '/internal/ping'
	queue_status = '/queue/status'
	progress = '/sdapi/v1/progress?skip_current_image=false'
	options = '/sdapi/v1/options'
	txt2img = '/sdapi/v1/txt2img'
	skip = '/sdapi/v1/skip'
	interrupt = '/sdapi/v1/interrupt'
	memory = '/sdapi/v1/memory'

	refresh_checkpoints = '/sdapi/v1/refresh-checkpoints'
	refresh_vae = '/sdapi/v1/refresh-vae' # do along with checkpoints
	refresh_loras = '/sdapi/v1/refresh-loras' # embeddings, hypernetworks, loras

	get_checkpoints = '/sdapi/v1/sd-models'
	get_hypernetworks = '/sdapi/v1/hypernetworks'
	get_embeddings = '/sdapi/v1/embeddings'
	get_loras = '/sdapi/v1/loras'
	get_samplers = '/sdapi/v1/samplers'
	get_upscalers = '/sdapi/v1/upscalers'
	get_upscaler_modes = '/sdapi/v1/latent-upscale-modes'

	unload_active_checkpoint = '/sdapi/v1/unload-checkpoint'

class APIErrors:
	INSTANCE_NOT_AVAILABLE = "Stable Diffusion Instance is not available - failed to connect."
	JSON_DECODE_FAIL = "Failed to JSON decode response from Stable Diffusion Instance."

class SDTxt2ImgParams(BaseModel):
	checkpoint : str

	prompt : str
	negative : str

	steps : int = Field(25)
	cfg_scale : float = Field(7.0)
	sampler_name : str = Field('Eular a')

	width : int = Field(512)
	height : int = Field(512)
	seed : int = Field(-1)

	# batch_size : int = Field(1)
	# n_iter : int = Field(1)

class StableDiffusionAPI:
	endpoint : str
	busy : bool

	next_info_timestamp : int
	instance_info : dict
	next_sysinfo_timestamp : int
	sysinfo : dict

	headers : dict
	cookies : dict

	def __init__( self, endpoint : str ) -> None:
		self.endpoint = endpoint
		self.busy = False

		self.next_info_timestamp = -1
		self.instance_info = None
		self.next_sysinfo_timestamp = -1
		self.sysinfo = None

		self.headers = None
		self.cookies = None

	async def internal_get(self, path : str) -> tuple[bool, str]:
		async with aiohttp.ClientSession(headers=self.headers, cookies=self.cookies) as client:
			try:
				response = await client.get(f'{self.endpoint}{path}')
			except:
				return False, APIErrors.INSTANCE_NOT_AVAILABLE
			if response.status != 200:
				return False, "Stable Diffusion Instance has errored: " + (response.reason or "No reason was given.")
			return True, await response.text()

	async def internal_post(self, path : str, data : str = None, json : dict = None) -> tuple[bool, str]:
		async with aiohttp.ClientSession(headers=self.headers, cookies=self.cookies) as client:
			try:
				response = await client.post(f'{self.endpoint}{path}', data=data, json=json)
			except:
				return False, APIErrors.INSTANCE_NOT_AVAILABLE
			if response.status != 200:
				return False, "Stable Diffusion Instance has errored: " + (response.reason or "No reason was given.")
			return True, await response.text()

	async def is_available( self ) -> bool:
		'''Check if the stable diffusion instance is online.'''
		success, _ = await self.internal_get( APIEndpoints.ping )
		return success is True

	async def get_system_info( self ) -> tuple[bool, Union[str, dict]]:
		'''Get the system information for the instance.'''
		timestamp = time.time()
		if timestamp < self.next_info_timestamp:
			return True, self.last_sysinfo

		success, sys_info_raw = await self.internal_get(
			APIEndpoints.sysinfo
		)

		if success is False:
			return False, sys_info_raw

		sys_info : dict = json.loads(sys_info_raw)

		torch_info = sys_info.get('Torch env info')
		if isinstance(torch_info, dict) is True:
			CPUINFO : dict = sys_info.get('CPU')
			if CPUINFO != None:
				CPUINFO.pop('model')
			try:
				CPUINFO['name'] = torch_info['cpu_info'][8].split('=')[1].strip()
			except:
				CPUINFO['name'] = 'unknown'
		else:
			CPUINFO = "unknown"

		self.next_sysinfo_timestamp = timestamp + 60 # 60 second interval
		self.sysinfo = {
			"OS" : type(torch_info) == dict and torch_info.get('os') or 'Unknown',
			"RAM" : sys_info.get('RAM'),
			"CPU" : CPUINFO,
			"GPUs" : type(torch_info) == dict and torch_info.get('nvidia_gpu_models') or None,
			"PythonVersion" : type(torch_info) == dict and torch_info.get('python_version').split(' ')[0] or None,
			"TorchVersion" : type(torch_info) == dict and torch_info.get('torch_version') or None,
			# "CmdLineArgs" : sys_info.get('Commandline')[1:],
			# "Extensions" : [ext.get('name') for ext in sys_info.get('Extensions')],
		}

		return True, self.sysinfo

	async def get_options( self ) -> tuple[bool, Union[str, dict]]:
		success, response = await self.internal_get(APIEndpoints.options)
		if success is False:
			return False, APIErrors.INSTANCE_NOT_AVAILABLE

		try:
			data = json.loads(response)
		except:
			return False, APIErrors.JSON_DECODE_FAIL

		return True, data

	async def update_options( self, options : dict ) -> tuple[bool, Union[str, dict]]:
		'''Update the stable diffusion options:'''
		success, data = await self.get_options()
		if success is False:
			return False, data

		try:
			data.update( options )
		except Exception as exception:
			return False, f'Failed to update stable diffusion instance options due to exception:\n{exception}'

		success, response = await self.internal_post(APIEndpoints.options, json=data)
		if success is False:
			return False, f'Failed to update stable diffusion instance options due to error: {response}'

		return True, 'Stable diffusion instance options were updated.'

	async def refresh_info( self ) -> tuple[bool, list]:
		'''
		Refresh all the stable diffusion information, which includes:
		- Checkpoints
		- LORAs (hypernetworks, loras, embeddings)
		- Upscalers
		'''
		# TODO: asyncio.gather?
		hasNotErrored : bool = True
		errorList : list[Union[str, None]] = []
		for path in [ APIEndpoints.refresh_checkpoints, APIEndpoints.refresh_vae, APIEndpoints.refresh_loras ]:
			success, response = await self.internal_post( path )
			if success is False:
				hasNotErrored = False
				errorList.append(response)
			else:
				errorList.append(None)
		return hasNotErrored, errorList

	async def get_instance_info( self ) -> Union[dict, None]:
		'''
		Get all the stable diffusion information, which includes:
		- Checkpoints
		- LORAs (hypernetworks, loras, embeddings)
		- Upscalers & Modes
		- Samplers
		'''

		timestamp = time.time()
		if timestamp < self.next_info_timestamp:
			return self.instance_info

		available : bool = await self.is_available()
		if available is False:
			return None

		base_info : dict[str, list] = {
			"checkpoints" : None,
			"hypernetworks" : None,
			"embeddings" : None,
			"loras" : None,
			"upscalers" : None,
			"upscaler_modes" : None,
			"samplers" : None
		}

		async def parse_endpoint( endpoint : str ) -> Union[list, dict, None]:
			success, response = await self.internal_get(endpoint)
			if success is False:
				return None
			try:
				return json.loads(response)
			except:
				return None

		# TODO: asyncio.gather?

		# checkpoints
		checkpoints : list[dict] = await parse_endpoint( APIEndpoints.get_checkpoints )
		if checkpoints is not None:
			base_info["checkpoints"] = [ {
				'title' : chpt['title'],
				'model_name' : chpt['model_name']
			} for chpt in checkpoints ]

		# embeddings
		embeddings : dict = await parse_endpoint( APIEndpoints.get_embeddings )
		if embeddings is not None:
			base_info['embeddings'] = list( embeddings['loaded'].keys() )

		# loras
		loras : list[dict] = await parse_endpoint( APIEndpoints.get_loras )
		if loras is not None:
			base_info['loras'] = [ data['name'] for data in loras ]

		# upscalers
		upscalers : list[dict] = await parse_endpoint( APIEndpoints.get_upscalers )
		if upscalers is not None:
			base_info['upscalers'] = [ data['name'] for data in upscalers ]

		# upscaler modes
		upscaler_modes : list[dict] = await parse_endpoint( APIEndpoints.get_upscaler_modes )
		if upscaler_modes is not None:
			base_info['upscaler_modes'] = [ data['name'] for data in upscaler_modes ]

		# samplers
		samplers : list[dict] = await parse_endpoint( APIEndpoints.get_samplers )
		if samplers is not None:
			base_info['samplers'] = [ data['name'] for data in samplers ]

		self.next_info_timestamp = timestamp + 60
		self.instance_info = base_info

		return base_info

	async def skip_operation( self ) -> bool:
		'''Skip the current operation.'''
		success, _ = await self.internal_post( APIEndpoints.skip )
		return success

	async def interrupt_operation( self ) -> bool:
		'''Interrupt the current operation.'''
		success, _ = await self.internal_post( APIEndpoints.interrupt )
		return success

	async def get_memory( self ) -> tuple[bool, Union[str, dict]]:
		'''Get memory information'''
		success, response = await self.internal_get(APIEndpoints.memory)
		if success is False:
			return False, APIErrors.INSTANCE_NOT_AVAILABLE
		try:
			return True, json.loads(response)
		except:
			return False, APIErrors.JSON_DECODE_FAIL

	async def unload_active_checkpoint( self ) -> bool:
		'''Unload the active checkpoint in memory.'''
		success, _ = await self.internal_post( APIEndpoints.unload_active_checkpoint )
		return success is True

	async def get_progress( self ) -> tuple[bool, Union[str, dict]]:
		'''Get the current generation progress'''
		success, response = await self.internal_get(APIEndpoints.progress)
		if success is False:
			return False, APIErrors.INSTANCE_NOT_AVAILABLE

		try:
			data : dict = json.loads(response)
		except:
			return False, APIErrors.JSON_DECODE_FAIL

		pop_indexes(data, ['current_image', 'textinfo', 'state'])
		if 'eta_relative' in data:
			data['eta'] = round(data.pop('eta_relative'), 3)

		return True, data

	async def get_queue_status( self ) -> tuple[bool, Union[str, dict]]:
		'''Get the current queue status'''
		success, response = await self.internal_get(APIEndpoints.progress)
		if success is False:
			return False, APIErrors.INSTANCE_NOT_AVAILABLE

		try:
			return True, json.loads(response)
		except:
			return False, APIErrors.JSON_DECODE_FAIL

	async def text2image( self, parameters : SDTxt2ImgParams ) -> tuple[bool, Union[str, dict]]:
		'''Query a text2image generation with given parameters.'''
		params : dict = parameters.model_dump()
		checkpoint : str = params.pop('checkpoint')

		success, response = await self.update_options({
			'sd_model_checkpoint': checkpoint
		})

		if success is False:
			return False, f'Failed to load checkpoint {checkpoint} due to:\n{response}'

		self.busy = True
		success, response = await self.internal_post(APIEndpoints.txt2img, json=params)
		self.busy = False

		if success is False:
			return False, f'Failed to queue txt2img request due to an error:\n{response}'

		try:
			return True, json.loads(response) # returns the images
		except:
			return False, APIErrors.JSON_DECODE_FAIL

class OperationStatus(Enum):
	NON_EXISTANT = 0
	IN_QUEUE = 1
	IN_PROGRESS = 2
	COMPLETED = 3

class Operation:
	uuid : str = Field(default_factory=lambda : uuid4().hex)
	state : int = Field(OperationStatus.NON_EXISTANT.value)

# class SDImage(BaseModel):
# 	'''A Generated Stable Diffusion Image.'''
# 	size : str
# 	data : str

# class SDSubItem(BaseModel):
# 	'''An item in queue for generation (no image data).'''
# 	uuid : str = Field(default_factory=lambda : uuid4().hex)
# 	error : str = Field(None)
# 	completed : bool = Field(False)
# 	generating : bool = Field(False)
# 	canceled : bool = Field(False)
# 	timestamp : str = Field(default_factory=tztimestamp)
# 	params : SDTxt2ImgParams = Field(None)

# class SDItem(SDSubItem):
# 	'''An item in queue for generation.'''
# 	images : list[SDImage] = Field(default_factory=list)

class StableDiffusionDistributor:

	endpoints : list[StableDiffusionAPI]
	operations : dict[str, Operation]

	def __init__( self ) -> None:
		self.endpoints = list()

	# queue : list[SDItem]
	# results : dict[str, SDItem]

	# def __init__( self ) -> None:
	# 	self.queue = list()
	# 	self.results = dict()

	# async def get_operation_metadata( self, unique : str, hide_params : bool = False ) -> Union[SDSubItem, None]:
	# 	'''Get the operation's metadata'''
	# 	value : SDItem = self.results.get(unique)
	# 	if value is None:
	# 		return None
	# 	try:
	# 		value = SDSubItem.model_validate(value, strict=False)
	# 		if hide_params is True:
	# 			value.params = None
	# 		return value
	# 	except Exception as exception:
	# 		print(f'Failed to convert "SDItem" model to "SDSubItem" model:\n{exception}')
	# 		return None

	# async def get_operation_images( self, unique : str ) -> Union[list[SDImage], None]:
	# 	'''Get the target operation images (if available)'''
	# 	value : SDItem = self.results.get(unique)
	# 	if value is None:
	# 		return None
	# 	return value.images

	# async def clear_operation( self, unique : str ) -> None:
	# 	'''Clear the operation from memory'''
	# 	if unique in self.results:
	# 		self.results.pop(unique)

	pass

if __name__ == '__main__':

	async def main() -> None:
		instance = StableDiffusionAPI('http://127.0.0.1:7860')

		success, response = await instance.get_memory()
		print(response)

	asyncio.run(main())
