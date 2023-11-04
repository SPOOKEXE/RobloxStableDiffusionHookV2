
import traceback
import numpy
import zlib
import json

from distributor import DistributorAPI, DistributorInstance, OperationStatus
from stablediffusion import StableDiffusionAPI, StableDiffusionInstance
from ccrypto import generate_random_key, encode_base64_hex, decode_base64_hex
from network import ServerThreadWrapper, setup_local_host, Ngrok, ThreadedServerResponder
from image import compress_image_complete, load_image_from_sd

from PIL import Image
from typing import Any
from time import sleep

def compress_str_transmission( value : str ) -> str:
	return zlib.compress( bytes( value.strip(), encoding='utf-8' ), level=9 ).hex()

def decompress_json_transmission( value : str ) -> dict:
	return json.loads( zlib.decompress( bytes.fromhex( value ) ) )

def prepare_compressed_image( image_raw : str ) -> tuple:
	# load to image and reduce size
	image : Image.Image = load_image_from_sd( image_raw )
	image.thumbnail((256,256))
	# compress image
	print( 'Preparing compressed image:', image.size, len(str( numpy.array(image).tolist() ).replace(' ', '')) )
	size, color_pallete, encoded_pixels = compress_image_complete( image, round_n=5, min_usage_count=3 )
	return size, compress_str_transmission( (str(color_pallete) + "|" + str(encoded_pixels)).replace(' ', '') )

def local_distribute_test( ) -> None:

	from time import sleep

	print('Setting up stable diffusion instances:')
	stable_diffusion_instances = [
		StableDiffusionInstance(url='http://127.0.0.1:7861')
	]

	print('Setting up distributor instance:')
	distributor = DistributorInstance(sd_instances=stable_diffusion_instances)

	none_working_instances = DistributorAPI.check_stable_diffusion_instances( distributor )
	if len(none_working_instances) > 0:
		print("Unavailable stable diffusion urls: ", *[ sd_inst.url for sd_inst in none_working_instances ])

	print('Send Text2Img')
	hash_id = DistributorAPI.distribute_text2img(distributor, {
		'username' : 'SPOOK_EXE',

		'checkpoint' : 'v1-5-pruned-emaonly.safetensors [6ce0161689]',

		'prompt' : 'pug',
		'negative_prompt' : 'bad quality',
		'steps' : 20,
		'cfg_scale' : 7,
		'sampler_name' : 'Euler a',

		'width' : 512,
		'height' : 512,
		'seed' : -1,

		# 'batch_size' : 1,
		# 'n_iter' : 1,
	})

	assert hash_id, 'No hash id was returned.'

	print('Awaiting completion or failure of hash id: ', hash_id)

	def get_state_str( state : OperationStatus ) -> str:
		return state == OperationStatus.NonExistent and 'NonExistent' or state == OperationStatus.InQueue and 'InQueue' or state == OperationStatus.InProgress and 'InProgress' or 'Finished'

	state = DistributorAPI.get_hash_status( distributor, hash_id )
	print( state, get_state_str(state) )
	assert state != OperationStatus.NonExistent, 'HashId does not exist in any stable diffusion instances.'

	print( DistributorAPI.get_operation_queue_info( distributor, hash_id ) )

	while state != OperationStatus.NonExistent and state != OperationStatus.Finished:
		sleep(0.2)
		state = DistributorAPI.get_hash_status( distributor, hash_id )
		print( state, get_state_str(state) )
		if state == OperationStatus.InProgress:
			print( DistributorAPI.get_operation_progress( distributor, hash_id ) )

	if state == OperationStatus.Finished:
		print('Getting image from hash id: ')
		image = DistributorAPI.get_hash_id_image( distributor, hash_id, pop_cache=True )
		print( len(image) )
	else:
		print('Image failed to be generated.')

def run_roblox_http_server( port : int = 500, sd_urls : list = [] ) -> ServerThreadWrapper:
	print('Setting up stable diffusion instances:')
	stable_diffusion_instances = [ StableDiffusionInstance(url=url) for url in sd_urls ]

	print('Setting up distributor instance:')
	distributor = DistributorInstance( sd_instances=stable_diffusion_instances )

	none_working_instances = DistributorAPI.check_stable_diffusion_instances( distributor )
	if len(none_working_instances) > 0:
		print("Unavailable stable diffusion urls: ", *[ sd_inst.url for sd_inst in none_working_instances ])

	def get_hash_image( distributor : DistributorInstance, hash_id : str ) -> str | None:
		img = DistributorAPI.get_hash_id_image( distributor, hash_id, pop_cache=True )
		if img == None:
			return None
		# index 1 is the image data (index 0 is the size tuple which can be discarded)
		return prepare_compressed_image( img )[1]

	ENDPOINTS = {
		"get_sd_instances" : lambda _, __ : DistributorAPI.get_stable_diffusion_instance_infos( distributor ),
		"get_hash_status" : lambda _, content : DistributorAPI.get_hash_status( distributor, content.get('hash') ),
		"get_hash_progress" : lambda _, content : DistributorAPI.get_operation_progress( distributor, content.get('hash') ),
		"get_hash_queue" : lambda _, content : DistributorAPI.get_operation_queue_info( distributor, content.get('hash') ),
		"get_hash_image" : lambda _, content : get_hash_image( distributor, content.get('hash') ),
		"post_txt2img" : lambda _, content : DistributorAPI.distribute_text2img( distributor, decompress_json_transmission( content.get('prompt') ), forceIndex=content.get('index') ),
	}

	def on_post( self : ThreadedServerResponder, _ : int, content : str ) -> tuple[int, Any]:
		try:
			content = json.loads(content)
		except:
			return 400, json.dumps({"message": "invalid json"})

		command : str = content.get('command')
		if command == None:
			return 400, json.dumps({"message": "no command parameter"})

		response_message = json.dumps({"message": "unknown command"})
		callback = ENDPOINTS.get(command)
		if callback != None:
			# print(content)
			try:
				value = callback( self, content )
				# print(value)
				response_message = json.dumps({
					"data" : compress_str_transmission(json.dumps([value])) 
				})
			except Exception as exception:
				print( 'Server Error: Failed to call ENDPOINT callback.' )
				print( traceback.print_exception(exception) )
				response_message = json.dumps({ "message" : 'server error: calling endpoint errored.' })
		return 200, response_message

	def on_get( _ : ThreadedServerResponder, __ : int, ___ : str ) -> tuple[int, Any]:
		return 200, json.dumps({'message' : 'You cannot access this server using GET.'})

	print("Webserver Started")
	return setup_local_host( port=port, onGET=on_get, onPOST=on_post )

if __name__ == '__main__':

	# from threading import Thread
	# t = Thread(target=local_distribute_test)
	# t.start()
	# t.join()

	# import requests

	webserver = run_roblox_http_server(
		port=500,
		sd_urls=['http://127.0.0.1:7860']
	)

	# Ngrok.set_port(webserver.webserver.server_port)
	# Ngrok.open_tunnel()

	# print("Ngrok Public Address: ", Ngrok.get_ngrok_addr())
	# print("Set the server address to the ngrok public address.")

	# response = requests.post('http://127.0.0.1:500', json={
	# 	'command' : 'get_sysinfo',
	# })
	# with open('dump.json', 'w') as file:
	# 	file.write( json.dumps( response.json(), indent=4 ) )

	while True:
		try:
			sleep(1/60)
		except KeyboardInterrupt:
			break
		except Exception:
			break

	# Ngrok.close_tunnel()
	webserver.shutdown()

	print("Webserver Closed")
