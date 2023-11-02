
import numpy
import zlib
import json

from distributor import DistributorAPI, DistributorInstance, OperationStatus
from stablediffusion import StableDiffusionAPI, StableDiffusionInstance
from ccrypto import generate_random_key, aes_decrypt, aes_encrypt, encode_base64_hex, decode_base64_hex
from network import SetupLocalHost, Ngrok, ThreadedServerResponder
from image import compress_image_complete, load_image_from_sd

from PIL import Image

def compress_str_transmission( value : str ) -> str:
	return zlib.compress( bytes( value.replace(' ', '').strip(), encoding='utf-8' ), level=9 ).hex()

def decompress_json_transmission( value : str ) -> dict:
	return json.loads( zlib.decompress( bytes.fromhex( value ) ) )

def prepare_compressed_image( image_raw : str ) -> tuple:
	# load to image and reduce size
	image : Image.Image = load_image_from_sd( image_raw )
	image.thumbnail((256,256))
	# compress image
	print( 'Preparing compressed image: ', image.size, len(str( numpy.array(image).tolist() ).replace(' ', '')) )
	size, color_pallete, encoded_pixels = compress_image_complete( image, round_n=5, min_usage_count=3 )
	return size, compress_str_transmission( str(color_pallete) + "|" + str(encoded_pixels) )

def local_distribute_test( ) -> None:

	from time import sleep

	print('Setting up stable diffusion instances:')
	stable_diffusion_instances = [
		StableDiffusionInstance(url='http://127.0.0.1:7860')
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

	state = DistributorAPI.is_hash_ready( distributor, hash_id )
	print( state, get_state_str(state) )
	assert state != OperationStatus.NonExistent, 'HashId does not exist in any stable diffusion instances.'

	print( DistributorAPI.get_operation_queue_info( distributor, hash_id ) )

	while state != OperationStatus.NonExistent and state != OperationStatus.Finished:
		sleep(0.2)
		state = DistributorAPI.is_hash_ready( distributor, hash_id )
		print( state, get_state_str(state) )
		if state == OperationStatus.InProgress:
			print( DistributorAPI.get_operation_progress( distributor, hash_id ) )

	if state == OperationStatus.Finished:
		print('Getting image from hash id: ')
		image = DistributorAPI.get_hash_id_image( distributor, hash_id, pop_cache=True )
		print( len(image) )
	else:
		print('Image failed to be generated.')

if __name__ == '__main__':

	from threading import Thread

	t = Thread(target=local_distribute_test)
	t.start()

	t.join()
