
import requests

from dataclasses import dataclass, field
from typing import Any, Callable
from time import time

def pop_indexes( array : list, indexes : list ) -> None:
	for idx in indexes:
		try:
			array.pop(idx)
		except:
			pass

def get_shortened_path( path : str ) -> str:
	return "\\".join( path.split('\\')[-3:] )

@dataclass
class StableDiffusionInstance:
	'''
	A stable diffusion instance:
	- url > the url to the stable diffusion webui?
	- queue > the operation hash queue?
	- busy > is the instance busy with a generation operation?
	- images > all the images cached for the given instance
	----
	- headers > the headers passed for requests to the instance
	- cookies > the cookies passed for requests to the instance
	'''
	url : str = None
	busy : bool = False
	queue : list = field(default_factory=list)
	errored_ids : list[str] = field(default_factory=list)
	images : dict = field(default_factory=dict)

	last_info_timestamp : int = 0
	last_info : dict = field(default_factory=dict)
	last_sysinfo_timestamp : int = 0
	last_sysinfo : dict = field(default_factory=dict)

	headers : dict = None
	cookies : dict = None

class APIErrorMessages:
	'''
	Error messages for the stable diffusion api
	'''
	connection_error = 'Connection Error - Could not connect to the stable diffusion instance: {}'
	server_error = 'Server Error: Could not connect to the stable diffusion instance: {}'

class APIEndpoints:
	'''
	Endpoints for the Stable Diffusion WebUI API
	'''
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

class StableDiffusionAPI:
	'''
	The core api to access a stable diffusion webui instance utilizing the stable diffusion instance class.
	'''

	@staticmethod
	def _internal_request(
		func : Callable[[str], tuple[bool, Any]],
		url : str,
		json : dict = None,
		headers : dict = None,
		cookies : dict = None
	) -> tuple[bool, Any]:
		'''
		Internal request method for the stable diffusion api:
		- requests.get
		- requests.post
		- requests.options
		- requests.patch
		- requests.delete
		- requests.put
		'''
		try:
			response : requests.Response = func( url, json=json, headers=headers, cookies=cookies, stream=False )
			return True, response.json()
		except requests.ConnectionError as exception:
			print( APIErrorMessages.connection_error.format( url ) )
			print( exception )
			return False, APIErrorMessages.connection_error.format( url )
		except Exception as exception:
			print( APIErrorMessages.server_error.format( url ) )
			print( exception )
			return False, APIErrorMessages.server_error.format( url )

	@staticmethod
	def is_sd_instance_online( sd_instance : StableDiffusionInstance ) -> bool:
		'''
		Check if the stable diffusion instance is online.
		'''
		assert sd_instance.url != None, 'The url for the stable diffusion instance has not been set.'
		success, _ = StableDiffusionAPI._internal_request(
			requests.get,
			f'{sd_instance.url}{APIEndpoints.ping}',
			headers=sd_instance.headers,
			cookies=sd_instance.cookies
		)
		return success

	@staticmethod
	def get_sd_instance_system_info( sd_instance : StableDiffusionInstance ) -> tuple[bool, Any]:
		'''
		Get the system information for the stable diffusion instance.
		'''

		timestamp = time()
		if timestamp < sd_instance.last_sysinfo_timestamp:
			return True, sd_instance.last_sysinfo

		success, sys_info = StableDiffusionAPI._internal_request(
			requests.get,
			f'{sd_instance.url}{APIEndpoints.sysinfo}',
			headers=sd_instance.headers,
			cookies=sd_instance.cookies
		)

		if (success == False) or (type(sys_info) != dict):
			return False, sys_info

		torch_info = sys_info.get('Torch env info')
		if type(torch_info) == dict:
			CPUINFO = sys_info.get('CPU')
			if CPUINFO != None:
				CPUINFO.pop('model')
			try:
				CPUINFO['name'] = torch_info['cpu_info'][8].split('=')[1].strip()
			except:
				CPUINFO['name'] = 'unknown'
		else:
			CPUINFO = "unknown"

		sd_instance.last_sysinfo_timestamp = timestamp + 30 # 30 second interval
		sd_instance.last_sysinfo = {
			"OS" : type(torch_info) == dict and torch_info.get('os') or 'Unknown',
			"RAM" : sys_info.get('RAM'),
			"CPU" : CPUINFO,
			"GPUs" : type(torch_info) == dict and torch_info.get('nvidia_gpu_models') or None,
			"PythonVersion" : type(torch_info) == dict and torch_info.get('python_version').split(' ')[0] or None,
			"TorchVersion" : type(torch_info) == dict and torch_info.get('torch_version') or None,
			"CmdLineArgs" : sys_info.get('Commandline')[1:],
			"Extensions" : [ ext.get('name') for ext in sys_info.get('Extensions') ],
		}

		return True, sd_instance.last_sysinfo

	@staticmethod
	def update_sd_instance_options( sd_instance : StableDiffusionInstance, options : dict ) -> tuple[bool, Any]:
		'''
		Update the stable diffusion options:
		'''
		success, values = StableDiffusionAPI._internal_request(
			requests.get,
			f'{sd_instance.url}{APIEndpoints.options}',
			headers=sd_instance.headers,
			cookies=sd_instance.cookies
		)

		if success == False:
			print( 'Failed to get stable diffusion instance options:\n{}'.format(values) )
			return False, 'Failed to get stable diffusion instance options:\n{}'.format(values)

		try:
			values.update( options )
		except Exception as exception:
			print( 'Failed to update options table: {}'.format( str(exception) ) )
			return False, 'Failed to update options table: {}'.format( str(exception) )

		return StableDiffusionAPI._internal_request(
			requests.post,
			f'{sd_instance.url}{APIEndpoints.options}',
			json=values,
			headers=sd_instance.headers,
			cookies=sd_instance.cookies
		)

	@staticmethod
	def refresh_sd_instance_info( sd_instance  : StableDiffusionInstance ) -> tuple[bool, Any]:
		'''
		Refresh all the stable diffusion information, which includes:
		- Checkpoints
		- LORAs (hypernetworks, loras, embeddings)
		- Upscalers
		'''
		wasSuccessful = True
		errorMessage = None
		for endpoint in [ APIEndpoints.refresh_checkpoints, APIEndpoints.refresh_vae, APIEndpoints.refresh_loras ]:
			success, error = StableDiffusionAPI._internal_request(
				requests.post,
				f'{sd_instance.url}{endpoint}',
				headers=sd_instance.headers,
				cookies=sd_instance.cookies
			)
			if success == False:
				print('Failed to refresh stable diffusion instance info: {}\n{}'.format(sd_instance.url, error))
				wasSuccessful = success
				errorMessage = error
		return wasSuccessful, errorMessage

	@staticmethod
	def get_sd_instance_info( sd_instance : StableDiffusionInstance ) -> tuple[bool, dict]:
		'''
		Get all the stable diffusion information, which includes:
		- Checkpoints
		- LORAs (hypernetworks, loras, embeddings)
		- Upscalers & Modes
		- Samplers
		'''

		timestamp = time()
		if timestamp < sd_instance.last_info_timestamp:
			return True, sd_instance.last_info

		base_info = {
			"checkpoints" : None,
			"hypernetworks" : None,
			"embeddings" : None,
			"loras" : None,
			"upscalers" : None,
			"upscaler_modes" : None,
			"samplers" : None
		}

		# checkpoints
		success, value = StableDiffusionAPI._internal_request(
			requests.get,
			f'{sd_instance.url}{APIEndpoints.get_checkpoints}',
			headers=sd_instance.headers,
			cookies=sd_instance.cookies
		)
		if success:
			base_info['checkpoints'] = [ {
				'title' : chpt['title'],
				'model_name' : chpt['model_name']
			} for chpt in value ]
		else:
			print('Failed to get checkpoints from the stable diffusion instance: ', value)

		# hypernetworks
		success, value = StableDiffusionAPI._internal_request(
			requests.get,
			f'{sd_instance.url}{APIEndpoints.get_hypernetworks}',
			headers=sd_instance.headers,
			cookies=sd_instance.cookies
		)
		if success:
			base_info['hypernetworks'] = [ data['name'] for data in value ]
		else:
			print('Failed to get hypernetworks from the stable diffusion instance: ', value)

		# embeddings
		success, value = StableDiffusionAPI._internal_request(
			requests.get,
			f'{sd_instance.url}{APIEndpoints.get_embeddings}',
			headers=sd_instance.headers,
			cookies=sd_instance.cookies
		)
		if success:
			base_info['embeddings'] = list( value['loaded'].keys() )
		else:
			print('Failed to get embeddings from the stable diffusion instance: ', value)

		# loras
		success, value = StableDiffusionAPI._internal_request(
			requests.get,
			f'{sd_instance.url}{APIEndpoints.get_loras}',
			headers=sd_instance.headers,
			cookies=sd_instance.cookies
		)

		if success:
			base_info['loras'] = [ data['name'] for data in value ]
		else:
			print('Failed to get loras from the stable diffusion instance: ', value)

		# upscalers
		success, value = StableDiffusionAPI._internal_request(
			requests.get,
			f'{sd_instance.url}{APIEndpoints.get_upscalers}',
			headers=sd_instance.headers,
			cookies=sd_instance.cookies
		)
		if success:
			base_info['upscalers'] = [ data['name'] for data in value ]
		else:
			print('Failed to get upscalers from the stable diffusion instance: ', value)

		# upscaler modes
		success, value = StableDiffusionAPI._internal_request(
			requests.get,
			f'{sd_instance.url}{APIEndpoints.get_upscaler_modes}',
			headers=sd_instance.headers,
			cookies=sd_instance.cookies
		)
		if success:
			base_info['upscaler_modes'] = [ data['name'] for data in value ]
		else:
			print('Failed to get upscaler_modes from the stable diffusion instance: ', value)

		# samplers
		success, value = StableDiffusionAPI._internal_request(
			requests.get,
			f'{sd_instance.url}{APIEndpoints.get_samplers}',
			headers=sd_instance.headers,
			cookies=sd_instance.cookies
		)
		if success:
			base_info['samplers'] = [ data['name'] for data in value ]
		else:
			print('Failed to get samplers from the stable diffusion instance: ', value)

		sd_instance.last_info_timestamp = timestamp + 30 # 30 second interval
		sd_instance.last_info = base_info
		return True, base_info

	@staticmethod
	def skip_sd_instance_operation( sd_instance : StableDiffusionInstance ) -> tuple[bool, Any]:
		'''
		Skip the current operation in the given stable diffusion instance
		'''
		return StableDiffusionAPI._internal_request(
			requests.post,
			f'{sd_instance.url}{APIEndpoints.skip}',
			headers=sd_instance.headers,
			cookies=sd_instance.cookies
		)

	@staticmethod
	def interrupt_sd_instance_operation( sd_instance : StableDiffusionInstance ) -> tuple[bool, Any]:
		'''
		Interrupt the current operation in the given stable diffusion instance
		'''
		return StableDiffusionAPI._internal_request(
			requests.post,
			f'{sd_instance.url}{APIEndpoints.interrupt}',
			headers=sd_instance.headers,
			cookies=sd_instance.cookies
		)

	@staticmethod
	def get_sd_instance_memory_info( sd_instance : StableDiffusionInstance ) -> tuple[bool, Any]:
		'''
		Get the memory information of the given stable diffusion instance
		'''
		return StableDiffusionAPI._internal_request(
			requests.post,
			f'{sd_instance.url}{APIEndpoints.memory}',
			headers=sd_instance.headers,
			cookies=sd_instance.cookies
		)

	@staticmethod
	def reload_sd_instance_active_checkpoint( sd_instance : StableDiffusionInstance ) -> tuple[bool, Any]:
		'''
		Reload the active checkpoint in the given stable diffusion instance
		'''
		return StableDiffusionAPI._internal_request(
			requests.post,
			f'{sd_instance.url}{APIEndpoints.reload_active_checkpoint}',
			headers=sd_instance.headers,
			cookies=sd_instance.cookies
		)

	@staticmethod
	def unload_sd_instance_active_checkpoint( sd_instance : StableDiffusionInstance ) -> tuple[bool, Any]:
		'''
		Unload the active checkpoint in the given stable diffusion instance
		'''
		return StableDiffusionAPI._internal_request(
			requests.post,
			f'{sd_instance.url}{APIEndpoints.unload_active_checkpoint}',
			headers=sd_instance.headers,
			cookies=sd_instance.cookies
		)

	@staticmethod
	def get_sd_instance_progress( sd_instance : StableDiffusionInstance ) -> tuple[bool, Any]:
		'''
		Get the stable diffusion instance progress information
		'''
		success, response = StableDiffusionAPI._internal_request(
			requests.get,
			f'{sd_instance.url}{APIEndpoints.progress}',
			headers=sd_instance.headers,
			cookies=sd_instance.cookies
		)

		if not success:
			return False, response

		pop_indexes( response, ['current_image', 'textinfo', 'state'] )
		try:
			response['eta'] = round(response.pop('eta_relative'), 3)
		except:
			pass
		return True, response

	@staticmethod
	def get_sd_instance_queue_status( sd_instance : StableDiffusionInstance ) -> tuple[bool, Any]:
		return StableDiffusionAPI._internal_request(
			requests.get,
			f'{sd_instance.url}{APIEndpoints.queue_status}',
			headers=sd_instance.headers,
			cookies=sd_instance.cookies
		)

	@staticmethod
	def text2img( sd_instance : StableDiffusionInstance, arguments : dict ) -> tuple[bool, Any]:
		'''
		POST the text2image request to the stable diffusion instance.
		Returns the values given back from the POST request to the instance.
		'''
		success, err = StableDiffusionAPI.update_sd_instance_options(sd_instance, {
			'sd_model_checkpoint': arguments.get('checkpoint')
		})

		if not success:
			print('Failed to load target checkpoint:', err)
			return False, err
		return StableDiffusionAPI._internal_request( requests.post, f'{sd_instance.url}{APIEndpoints.txt2img}', json=arguments, headers=sd_instance.headers, cookies=sd_instance.cookies )

	@staticmethod
	def get_sd_instance_operation_image( sd_instance : StableDiffusionInstance, hash_id : str, pop_value : bool = False ) -> tuple[bool, Any]:
		'''
		Get the stable diffusion instance's generated image for a given operation hash
		'''
		return sd_instance.images.get( hash_id )
