
import io
import base64
import json
import numpy as np
import zlib

from distributor import DistributorAPI, DistributorInstance
from ccrypto import generate_random_key, aes_decrypt, aes_encrypt, encode_base64_hex, decode_base64_hex
from stablediffusion import StableDiffusionAPI, StableDiffusionInstance
from network import SetupLocalHost, Ngrok, ThreadedServerResponder
from image import compress_image_complete

from math import floor
from time import time
from os import makedirs
from PIL import Image
from time import sleep

def preprocesses_string( value : str ) -> str:
	return value.replace(' ', '').strip()

def prepare_compressed_image( image_raw : str ) -> tuple:
	# load to image
	image = Image.open( io.BytesIO( base64.b64decode(image_raw) ) ).convert('RGB')
	makedirs('img_cache', exist_ok=True)
	image.save('img_cache/' + str(floor(time())) + '.jpeg')
	# reduce size
	image.thumbnail((256,256))
	print( 'Preparing compressed image: ', image.size, len(str( np.array(image).tolist() ).replace(' ', '')) )
	# compress
	size, color_pallete, encoded_pixels = compress_image_complete( image, round_n=5, min_usage_count=3 )
	return size, zlib.compress( bytes( preprocesses_string( str(color_pallete) + "|" + str(encoded_pixels) ), encoding='utf-8' ), level=9 ).hex()

def get_operation_status( distributors : list[DistributorInstance], hash_id : str ) -> dict:
	pass

if __name__ == '__main__':

	print('Setting up stable diffusion instances:')
	stable_diffusion_instances = [
		StableDiffusionInstance(url='http://localhost:7860', queue=[], images={})
	]

	print('Setting up distributor instance:')
	distributor = DistributorInstance(sd_instances=stable_diffusion_instances, hash_id_cache=[])

	none_working_instances = DistributorAPI.check_stable_diffusion_instances( distributor )
	if len(none_working_instances) > 0:
		print("Unavailable stable diffusion urls: ", *[ sd_inst.url for sd_inst in none_working_instances ])

	print('Send Text2Img')
	hash_id = DistributorAPI.distribute_text2img(distributor, {
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

	print('Await completion or failure: ')
	state = DistributorAPI.is_hash_ready( distributor, hash_id )
	print( state )
	assert state == -1, 'HashId does not exist in any stable diffusion instances.'

	while state != -1 and state != 2:
		sleep(1)
		state = DistributorAPI.is_hash_ready( distributor, hash_id )
		print( state )
		assert state == -1, 'HashId does not exist in any stable diffusion instances.'

	print('Getting image from hash id: ')
	image = DistributorAPI.get_hash_id_image( distributor, hash_id, remove = True )
	print( len(image) )
