
import requests

from dataclasses import dataclass
from typing import Any, Callable

def pop_indexes( array : list, indexes : list ) -> None:
	for idx in indexes:
		try:
			array.pop(idx)
		except:
			pass

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
	queue : list = None
	images : dict = None

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
	progress = '/sdapi/v1/progress'
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
		func : Callable[[str], dict],
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
			return True, func( url, json=json, headers=headers, cookies=cookies ).json()
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
		success, sys_info = StableDiffusionAPI._internal_request(
			requests.get,
			f'{sd_instance.url}{APIEndpoints.sysinfo}',
			headers=sd_instance.headers,
			cookies=sd_instance.cookies
		)

		if success == False:
			return False, sys_info

		return True, {
			"Path" : sys_info.get('Data path'),
			"Extensions" : [ ext.get('name') for ext in sys_info.get('Extensions') ],
			"RAM" : sys_info.get('RAM'),
			"CPU" : sys_info.get('CPU'),
			"CmdLineArgs" : sys_info.get('Commandline')[1:]
		}

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
			f'{sd_instance}{APIEndpoints.get_checkpoints}',
			headers=sd_instance.headers,
			cookies=sd_instance.cookies
		)
		if success:
			base_info['checkpoints'] = value
		else:
			print('Failed to get checkpoints from the stable diffusion instance: ', value)

		# hypernetworks
		success, value = StableDiffusionAPI._internal_request(
			requests.get,
			f'{sd_instance}{APIEndpoints.get_hypernetworks}',
			headers=sd_instance.headers,
			cookies=sd_instance.cookies
		)
		if success:
			base_info['hypernetworks'] = value
		else:
			print('Failed to get hypernetworks from the stable diffusion instance: ', value)

		# embeddings
		success, value = StableDiffusionAPI._internal_request(
			requests.get,
			f'{sd_instance}{APIEndpoints.get_embeddings}',
			headers=sd_instance.headers,
			cookies=sd_instance.cookies
		)
		if success:
			base_info['embeddings'] = value
		else:
			print('Failed to get embeddings from the stable diffusion instance: ', value)

		# loras
		success, value = StableDiffusionAPI._internal_request(
			requests.get,
			f'{sd_instance}{APIEndpoints.get_loras}',
			headers=sd_instance.headers,
			cookies=sd_instance.cookies
		)
		if success:
			base_info['loras'] = value
		else:
			print('Failed to get loras from the stable diffusion instance: ', value)

		# upscalers
		success, value = StableDiffusionAPI._internal_request(
			requests.get,
			f'{sd_instance}{APIEndpoints.get_upscalers}',
			headers=sd_instance.headers,
			cookies=sd_instance.cookies
		)
		if success:
			base_info['upscalers'] = value
		else:
			print('Failed to get upscalers from the stable diffusion instance: ', value)

		# upscaler modes
		success, value = StableDiffusionAPI._internal_request(
			requests.get,
			f'{sd_instance}{APIEndpoints.get_upscaler_modes}',
			headers=sd_instance.headers,
			cookies=sd_instance.cookies
		)
		if success:
			base_info['upscaler_modes'] = value
		else:
			print('Failed to get upscaler_modes from the stable diffusion instance: ', value)

		# samplers
		success, value = StableDiffusionAPI._internal_request(
			requests.get,
			f'{sd_instance}{APIEndpoints.get_samplers}',
			headers=sd_instance.headers,
			cookies=sd_instance.cookies
		)
		if success:
			base_info['samplers'] = value
		else:
			print('Failed to get samplers from the stable diffusion instance: ', value)

		return True, base_info

	@staticmethod
	def skip_sd_instance_operation( sd_instance : StableDiffusionInstance ) -> tuple[bool, Any]:
		'''
		Skip the current operation in the given stable diffusion instance
		'''
		return StableDiffusionAPI._internal_request(
			requests.post,
			f'{sd_instance}{APIEndpoints.skip}',
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
			f'{sd_instance}{APIEndpoints.interrupt}',
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
			f'{sd_instance}{APIEndpoints.memory}',
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
			f'{sd_instance}{APIEndpoints.reload_active_checkpoint}',
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
			f'{sd_instance}{APIEndpoints.unload_active_checkpoint}',
			headers=sd_instance.headers,
			cookies=sd_instance.cookies
		)

	@staticmethod
	def get_sd_instance_progress( sd_instance : StableDiffusionInstance ) -> tuple[bool, Any]:
		'''
		Get the stable diffusion instance progress information
		'''
		success, response = StableDiffusionAPI._internal_request(
			requests.post,
			f'{sd_instance}{APIEndpoints.progress}',
			headers=sd_instance.headers,
			cookies=sd_instance.cookies
		)
		if not success:
			return False, response

		pop_indexes( response, ['current_image', 'textinfo'] )
		try:
			response['eta'] = response.pop('eta_relative')
		except:
			pass
		return True, response

	@staticmethod
	def get_sd_instance_queue_status( sd_instance : StableDiffusionInstance ) -> tuple[bool, Any]:
		return StableDiffusionAPI._internal_request(
			requests.post,
			f'{sd_instance}{APIEndpoints.queue_status}',
			headers=sd_instance.headers,
			cookies=sd_instance.cookies
		)

	@staticmethod
	def text2img( sd_instance : StableDiffusionInstance, arguments : dict ) -> str:
		success, err = StableDiffusionAPI.update_sd_instance_options(sd_instance, {
			'sd_model_checkpoint': arguments.get('checkpoint')
		})

		if not success:
			print('Failed to load target checkpoint:', err)
			return False, err

		success, err = StableDiffusionAPI._internal_request( requests.post, f'{sd_instance.url}{APIEndpoints.txt2img}', json=arguments, headers=sd_instance.headers, cookies=sd_instance.cookies )

	@staticmethod
	def get_sd_instance_operation_image( sd_instance : StableDiffusionInstance, operation_hash : str ) -> tuple[bool, Any]:
		'''
		Get the stable diffusion instance's generated image for a given operation hash
		'''
		pass

def update_sd_instances( instances : list[StableDiffusionInstance] ) -> None:
	'''
	Update all passed stable diffusion instances
	'''
	pass
