
import requests

from typing import Any, Callable
from time import time
from enum import Enum

def pop_indexes( d : dict, indexes : list ) -> None:
	for idx in indexes:
		if idx in d:
			d.pop(idx)

class StableDiffusionAPI:
	'''
	The core api to access a stable diffusion webui instance utilizing the stable diffusion instance class.
	'''

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
