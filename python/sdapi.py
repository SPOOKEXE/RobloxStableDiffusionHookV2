
from __future__ import annotations
from uuid import uuid4
from pydantic import BaseModel, Field
from typing import Union
from enum import Enum
from PIL import Image
from threading import Thread
from io import BytesIO
from base64 import b64decode

import json
import datetime
import asyncio
import aiohttp
import time

OPERATION_AUTO_EXPIRY : int = 60 # time before operations are auto-deleted

def load_bs4_image( data : str ) -> Image.Image:
	return Image.open( BytesIO( b64decode(data) ) ).convert('RGB')

def timestamp() -> int:
	return int(round(datetime.datetime.now(datetime.timezone.utc).timestamp()))

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
	refresh_loras = '/sdapi/v1/refresh-loras' # embeddings, loras

	get_checkpoints = '/sdapi/v1/sd-models'
	get_embeddings = '/sdapi/v1/embeddings'
	get_loras = '/sdapi/v1/loras'
	get_samplers = '/sdapi/v1/samplers'

	unload_active_checkpoint = '/sdapi/v1/unload-checkpoint'

class APIErrors:
	INSTANCE_NOT_AVAILABLE = "Stable Diffusion Instance is not available - failed to connect."
	JSON_DECODE_FAIL = "Failed to JSON decode response from Stable Diffusion Instance."

class SDTxt2ImgParams(BaseModel):
	checkpoint : str = Field(None)

	prompt : str = Field(None)
	negative : str = Field(None)

	steps : int = Field(25)
	cfg_scale : float = Field(7.0)
	sampler_name : str = Field('Euler a')

	width : int = Field(512)
	height : int = Field(512)
	seed : int = Field(-1)

	# batch_size : int = Field(1)
	# n_iter : int = Field(1)

class StableDiffusionInstance:
	uuid : str
	endpoint : str
	busy : bool

	next_info_timestamp : int
	instance_info : dict
	next_sysinfo_timestamp : int
	sysinfo : dict

	headers : dict
	cookies : dict

	def __init__(
		self,
		endpoint : str,
		headers : dict = None,
		cookies : dict = None,
	) -> None:
		self.uuid = uuid4().hex
		self.endpoint = endpoint
		self.busy = False

		self.next_info_timestamp = -1
		self.instance_info = None
		self.next_sysinfo_timestamp = -1
		self.sysinfo = None

		self.headers = headers
		self.cookies = cookies

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
		- LORAs (loras, embeddings)
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
		- LORAs (loras, embeddings)
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
			"embeddings" : None,
			"loras" : None,
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
		print(params)
		success, response = await self.internal_post(APIEndpoints.txt2img, json=params)
		self.busy = False

		if success is False:
			return False, f'Failed to queue txt2img request due to an error:\n{response}'

		try:
			return True, json.loads(response) # returns the images
		except:
			return False, APIErrors.JSON_DECODE_FAIL

class OperationStatus(Enum):
	IN_QUEUE = 0
	IN_PROGRESS = 1
	COMPLETED = 2
	CANCELED = 3
	ERRORED = 4

class SDImage(BaseModel):
	'''A Generated Stable Diffusion Image.'''
	size : tuple[int, int] = Field(None)
	data : str = Field(None)

class Operation(BaseModel):
	# base
	uuid : str = Field(default_factory=lambda : uuid4().hex)
	state : int = Field(OperationStatus.IN_QUEUE.value)
	timestamp : int = Field(default_factory=timestamp)
	error : str = Field(None)
	# txt2img
	params : SDTxt2ImgParams = Field(None)
	results : list[SDImage] = Field(None)
	sdinstance : str = Field(None)

class StableDiffusionDistributor:
	instances : list[StableDiffusionInstance]
	operations : dict[str, Operation]
	queue : list[str]

	_active : bool
	_thread : Thread

	def __init__( self, instances : Union[list[StableDiffusionInstance], None] ) -> None:
		self.instances = instances if instances is not None else None
		self.operations = dict()
		self.queue = list()
		self._active = False
		self._thread = None

	async def find_unavailable_instances( self ) -> list[StableDiffusionInstance]:
		unavailable : list[StableDiffusionInstance] = []
		for instance in self.instances:
			available = await instance.is_available()
			if available is False:
				print(f"Stable Diffusion Instance is unavailable: {instance.endpoint}")
				unavailable.append( instance )
				self.instances.remove( instance )
		return unavailable

	async def get_instances_infos( self ) -> list[dict]:
		for instance in self.instances:
			_, _ = await instance.refresh_info()
		infos : list[dict] = []
		for instance in self.instances:
			_, sysinfo = await instance.get_system_info()
			instinfo = await instance.get_instance_info()
			infos.append({ "sys_info" : sysinfo, "sd_info" : instinfo })
		return infos

	async def _internal_txt2img(self, instance : StableDiffusionInstance, operation : Operation) -> None:
		instance.busy = True
		operation.state = OperationStatus.IN_PROGRESS.value
		operation.sdinstance = instance.uuid

		params = operation.params
		success, response = await instance.text2image(params)

		instance.busy = False
		if success is False:
			operation.error = response
			operation.state = OperationStatus.ERRORED.value
		else:
			size = (params.width, params.height)
			results = [ SDImage(data=image_bs4, size=size) for image_bs4 in response['images'] ]
			operation.results = results
			operation.state = OperationStatus.COMPLETED.value

	async def queue_txt2img( self, parameters : SDTxt2ImgParams ) -> Union[str, None]:
		operation = Operation(params=parameters)
		self.operations[operation.uuid] = operation
		self.queue.append(operation.uuid)
		return operation.uuid

	async def get_operation_sdinstance( self, operation_id : str ) -> Union[StableDiffusionInstance, None]:
		operation : Operation = self.operations.get(operation_id)
		if operation is None:
			return None
		uuid : str = operation.sdinstance
		if uuid is None:
			return None
		for instance in self.instances:
			if instance.uuid == uuid:
				return instance
		return None

	async def get_operation_status( self, operation_id : str ) -> Union[int, None]:
		operation : Operation = self.operations.get(operation_id, None)
		if operation is None:
			return None
		return operation.state

	async def is_operation_completed( self, operation_id : str ) -> bool:
		status = await self.get_operation_status(operation_id)
		return \
			status is None or \
			status == OperationStatus.CANCELED.value or \
			status == OperationStatus.ERRORED.value or \
			status == OperationStatus.COMPLETED.value

	async def get_operation_progress( self, operation_id : str ) -> Union[dict, None]:
		instance : StableDiffusionInstance = await self.get_operation_sdinstance(operation_id)
		if instance is None:
			return None
		success, response = await instance.get_progress()
		if success is True:
			return response
		return None

	async def get_operation_images( self, operation_id : str ) -> Union[list[Image.Image], None]:
		if operation_id in self.operations.keys():
			return self.operations[operation_id].results
		return None

	async def cancel_operation( self, operation_id : str ) -> None:
		if operation_id in self.queue:
			self.queue.remove(operation_id)
		operation : Operation = self.operations.get(operation_id)
		if operation is None:
			return
		instance = await self.get_operation_sdinstance( operation_id )
		if instance is None:
			return
		operation.state = OperationStatus.CANCELED.value
		operation.sdinstance = None
		_ = await instance.skip_operation()
		_ = await instance.interrupt_operation()
		instance.busy = False

	async def update_queue(self) -> None:
		# find free instances
		free_instances = [ instance for instance in self.instances if instance.busy is False ]
		if len(free_instances) == 0:
			return # no free instances, skip

		# remove any missing queued operation mappings
		index = 0
		while index < len(self.queue):
			operation_id : str = self.queue[index]
			operation = self.operations.get(operation_id)
			if operation is None:
				self.queue.pop(index)
			else:
				index += 1

		# run batch of coroutines to generate images
		coros = []
		quantity = min(len(free_instances), len(self.queue))
		while quantity > 0:
			quantity -= 1
			instance = free_instances.pop(0)
			operation_id = self.queue.pop(0)
			operation = self.operations[operation_id]
			coros.append(self._internal_txt2img( instance, operation ))
		await asyncio.gather(*coros)

	async def check_for_expired_operations(self) -> None:
		now = timestamp()
		for uuid in list(self.operations.keys()):
			operation = self.operations.get(uuid)
			if operation is None:
				continue
			if now - operation.timestamp > OPERATION_AUTO_EXPIRY:
				print(f'Operation {operation.uuid} has expired.')
				_ = self.operations.pop(uuid)

	async def initialize(self) -> None:
		def main_loop() -> None:
			asyncio.new_event_loop()
			while self._active is True:
				asyncio.run(self.check_for_expired_operations())
				asyncio.run(self.update_queue())
				time.sleep(3)
		await self.shutdown()
		self._active = True
		self._thread = Thread(target=main_loop)
		self._thread.start()

	async def shutdown(self) -> None:
		self._active = False
		if self._thread is not None:
			self._thread.join() # wait for closure
			self._thread = None

async def test() -> None:
	local_distributor = StableDiffusionDistributor([
		StableDiffusionInstance('http://127.0.0.1:7860')
	])

	await local_distributor.initialize()

	print(await local_distributor.instances[0].get_instance_info())

	params : SDTxt2ImgParams = SDTxt2ImgParams(
		checkpoint="analogmadnessrealisticmodel\\analogMadness_v70.safetensors [71652f47a2]",
		prompt="pug",
		negative="",
		steps=25,
		cfg_scale=7,
		sampler_name="Euler a",
		width=512,
		height=512,
		seed=1,
	)

	operation_id : Union[str, None] = await local_distributor.queue_txt2img(params)
	if operation_id is None:
		raise ValueError("Attempt to queue did not return a operation id.")

	while True:
		await asyncio.sleep(1)
		status : int = await local_distributor.get_operation_status(operation_id)
		print(OperationStatus(status).name)
		complete : bool = await local_distributor.is_operation_completed( operation_id )
		if complete is True:
			break
		print( await local_distributor.get_operation_progress(operation_id) )

	operation = local_distributor.operations.get(operation_id)
	if operation is None:
		raise ValueError("Could not find operation after queuing!")

	if status == OperationStatus.COMPLETED.value:
		images = await local_distributor.get_operation_images(operation_id)
		load_bs4_image(images[0]).show('Generated Image')
	elif status == OperationStatus.ERRORED.value:
		print(operation.error)

# if __name__ == '__main__':
# 	asyncio.run(test())
