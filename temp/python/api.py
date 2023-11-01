
import requests
import os
import _thread
import json
import time

from math import floor
from uuid import uuid4

STABLE_DIFFUSION_ADDRESS = "http://127.0.0.1:7860"

def get_sys_info( ) -> dict:
	data = requests.get(f'{STABLE_DIFFUSION_ADDRESS}/internal/sysinfo').json()
	return {
		"Path" : data['Data path'],
		"Extensions" : [ ext['name'] for ext in data['Extensions'] ],
		"RAM" : data['RAM'],
		"CPU" : data["CPU"],
		"CmdLineArgs" : data['Commandline'][1:]
	}

SYS_INFO = get_sys_info()
# TODO: find a resolution for this,
# just want it to output 'stable diffusion
# is not running'.
# try:
# 	SYS_INFO = get_sys_info()
# except requests.RequestException:
# 	raise SystemError("You must have stable diffusion running in the background.")

def refresh_checkpoints( ) -> None:
	requests.post(f'{STABLE_DIFFUSION_ADDRESS}/sdapi/v1/refresh-checkpoints')

def refresh_vae( ) -> None:
	requests.post(f'{STABLE_DIFFUSION_ADDRESS}/sdapi/v1/refresh-vae')

def refresh_loras( ) -> None:
	requests.post(f'{STABLE_DIFFUSION_ADDRESS}/sdapi/v1/refresh-loras')

def refresh_hypernetworks( ) -> None:
	refresh_loras( )

def refresh_embeddings( ) -> None:
	refresh_loras( )

def get_hypernetworks( ) -> list:
	refresh_hypernetworks( )
	hypernetworks = requests.get(f'{STABLE_DIFFUSION_ADDRESS}/sdapi/v1/hypernetworks').json()
	for network in hypernetworks:
		network['path'] = network.pop('path')[len(SYS_INFO['Path'])+1:]
	return hypernetworks

def get_embeddings( ) -> list:
	refresh_embeddings( )
	return requests.get(f'{STABLE_DIFFUSION_ADDRESS}/sdapi/v1/embeddings').json()['loaded']

def get_vaes( ) -> list:
	refresh_vae( )
	vaes = requests.get(f'{STABLE_DIFFUSION_ADDRESS}/sdapi/v1/sd-vae').json()
	for vae in vaes:
		vae['name'] = vae.pop('model_name')
		vae['path'] = vae.pop('filename')[len(SYS_INFO['Path'])+1:]
	return vaes

def get_checkpoints( ) -> list:
	refresh_checkpoints()
	return [ {
		"title" : model['title'],
		"model_name" : model['model_name'],
		"size_bytes" : os.path.getsize( model['filename'] )
	} for model in requests.get(
		f'{STABLE_DIFFUSION_ADDRESS}/sdapi/v1/sd-models'
	).json() ]

def get_loras( ) -> list:
	refresh_loras( )
	loras = requests.get(f'{STABLE_DIFFUSION_ADDRESS}/sdapi/v1/loras').json()
	for lora in loras:
		lora['path'] = lora['path'][len(SYS_INFO['Path'])+1:]
		meta = lora.pop('metadata')
		if len(list(meta.keys())) > 0 and meta.get( 'ss_network_module' ) != None:
			lora['type'] = meta['ss_network_module'].split('.')[-1]
		else:
			lora['type'] = 'unknown'
	return loras

def get_samplers( ) -> list:
	return [ item['name'] for item in requests.get(f'{STABLE_DIFFUSION_ADDRESS}/sdapi/v1/samplers').json() ]

def get_upscalers( ) -> list:
	return [ item['name'] for item in requests.get(f'{STABLE_DIFFUSION_ADDRESS}/sdapi/v1/upscalers').json() ]

def reload_checkpoint( ) -> None:
	requests.post(f'{STABLE_DIFFUSION_ADDRESS}/sdapi/v1/reload-checkpoint')

def unload_checkpoint( ) -> None:
	requests.post(f'{STABLE_DIFFUSION_ADDRESS}/sdapi/v1/unload-checkpoint')

def get_txt2img_scripts( ) -> list:
	return requests.get(f'{STABLE_DIFFUSION_ADDRESS}/sdapi/v1/scripts')['txt2img']

def set_prompt_options( options : dict ) -> None:
	return requests.post(f'{STABLE_DIFFUSION_ADDRESS}/sdapi/v1/options', json=options)

def get_prompt_options( ) -> dict:
	return requests.get(f'{STABLE_DIFFUSION_ADDRESS}/sdapi/v1/options').json()

def update_prompt_options( options : dict ) -> None:
	values = get_prompt_options( )
	values.update(options)
	set_prompt_options( values )

IMAGE_CACHE_HASHMAP = { }
ACTIVE_IMAGE_HASHES = [ ]

def get_operation_status( hash_id : str ) -> dict:
	global IMAGE_CACHE_HASHMAP, ACTIVE_IMAGE_HASHES
	if ACTIVE_IMAGE_HASHES.count( hash_id ) == 0:
		return { "status" : -1, "message" : "no such image in memory." }
	if ACTIVE_IMAGE_HASHES.count( hash_id ) > 0 and IMAGE_CACHE_HASHMAP.get( hash_id ) == None:
		return { "status" : 1, "message" : "image is still being processed." }
	return { "status" : 2, "message" : None }

def get_images_from_operation( hash_id : str ) -> list | None:
	return IMAGE_CACHE_HASHMAP.get( hash_id )

def txt2img(
	playerName : str = "None",
	checkpoint : str = "v1-5-pruned-emaonly.safetensors [6ce0161689]",
	checkpoint_vae : str = None,
	# embeddings : list[tuple] = None,
	# hypernetworks : list[tuple] = None,
	# loras : list[tuple] = None,

	prompt : str = "",
	negative_prompt : str = "",

	steps : int = 25,
	cfg_scale : int = 7,
	sampler_name : str = "Euler a",
	width : str = 512,
	height : str = 512,

	batch_size : int = 1,
	batch_count : int = 1,
	seed : int = -1,

	log_file : str = None
) -> str:

	if type(log_file) == str:
		new_data = json.dumps([ floor(time.time()), playerName, checkpoint, prompt, negative_prompt, sampler_name ]) + "\n"
		cmd = os.path.exists(log_file) and 'a' or 'w'
		with open(log_file, cmd) as file:
			file.write(new_data)

	# change models / vae
	update_prompt_options({
		'sd_model_checkpoint': checkpoint,
		'sd_vae' : checkpoint_vae
	})

	# run txt2img
	def request_txt2img( hash_id : str, data : dict ) -> None:
		global IMAGE_CACHE_HASHMAP
		ACTIVE_IMAGE_HASHES.append(hash_id)
		# print(data)
		response = requests.post(f"{STABLE_DIFFUSION_ADDRESS}/sdapi/v1/txt2img", json=data)
		# print( response.json() )
		IMAGE_CACHE_HASHMAP[hash_id] = response.json()['images']

	hash_id = uuid4().hex
	prompt_data = {
		"prompt" : prompt,
		"negative_prompt" : negative_prompt,
		"steps" : steps,
		"seed" : seed,
		"sampler_name" : 'Euler a',
		"batch_size" : batch_size,
		"n_iter" : batch_count,
		"cfg_scale" : cfg_scale,
		"width" : width,
		"height" : height
	}

	_thread.start_new_thread( request_txt2img, (hash_id, prompt_data) )
	return hash_id
