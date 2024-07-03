
import json
from uuid import uuid4
from pydantic import BaseModel, Field
from typing import Union

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

	reload_active_checkpoint = '/sdapi/v1/reload-checkpoint'
	unload_active_checkpoint = '/sdapi/v1/unload-checkpoint'

class SDImage(BaseModel):
	'''A Generated Stable Diffusion Image.'''
	size : str
	data : str

class SDItem(BaseModel):
	'''An item in queue for generation.'''
	uuid : str = Field(default_factory=lambda : uuid4().hex)
	error : str = Field(None)
	completed : bool = Field(False)
	generating : bool = Field(False)
	canceled : bool = Field(False)
	images : dict[str, SDImage] = Field(default_factory=dict)
	timestamp : str = Field(default_factory=tztimestamp)

class StableDiffusionAPI:
	endpoint : str
	busy : bool
	queue : list[SDItem]
	results : dict[str, SDItem]

	next_info_timestamp : int
	sdinfo : dict
	next_sysinfo_timestamp : int
	sysinfo : dict

	headers : dict
	cookies : dict

	def __init__( self, endpoint : str ) -> None:
		self.endpoint = endpoint
		self.busy = False
		self.queue = list()
		self.results = dict()

		self.next_info_timestamp = -1
		self.last_info = None
		self.next_sysinfo_timestamp = -1
		self.last_sysinfo = None

		self.headers = None
		self.cookies = None

	async def internal_get(self, path : str) -> tuple[bool, str]:
		async with aiohttp.ClientSession(headers=self.headers, cookies=self.cookies) as client:
			try:
				response = await client.get(f'{self.endpoint}{path}')
			except:
				return False, "Stable Diffusion Instance is not available - failed to connect."
			if response.status != 200:
				return False, "Stable Diffusion Instance has errored: " + (response.reason or "No reason was given.")
			return True, await response.text()

	async def internal_post(self, path : str, data : str = None, json : dict = None) -> tuple[bool, str]:
		async with aiohttp.ClientSession(headers=self.headers, cookies=self.cookies) as client:
			try:
				response = await client.post(f'{self.endpoint}{path}', data=data, json=json)
			except:
				return False, "Stable Diffusion Instance is not available - failed to connect."
			if response.status != 200:
				return False, "Stable Diffusion Instance has errored: " + (response.reason or "No reason was given.")
			return True, await response.text()

	async def is_available( self ) -> bool:
		'''Check if the stable diffusion instance is online.'''
		success, _ = await self.internal_get( APIEndpoints.ping )
		return success is True

	async def get_system_info( self, cache_duration : int = 60 ) -> tuple[bool, Union[str, dict]]:
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
		if type(torch_info) == dict:
			CPUINFO : dict = sys_info.get('CPU')
			if CPUINFO != None:
				CPUINFO.pop('model')
			try:
				CPUINFO['name'] = torch_info['cpu_info'][8].split('=')[1].strip()
			except:
				CPUINFO['name'] = 'unknown'
		else:
			CPUINFO = "unknown"

		self.next_sysinfo_timestamp = timestamp + cache_duration # 30 second interval
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

class StableDiffusionDistributor:
	pass

if __name__ == '__main__':

	async def main() -> None:
		instance = StableDiffusionAPI('http://127.0.0.1:7860')

		success, response = await instance.get_system_info()
		print(response)

	asyncio.run(main())
