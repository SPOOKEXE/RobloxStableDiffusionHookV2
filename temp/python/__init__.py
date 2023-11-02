
import io
import base64
import json
import numpy as np
import zlib

from PIL import Image
from time import sleep

from image import ( compress_image_complete, decompress_image_complete )
from certificate import ( GenerateDefaultCertificateBase64, ToBase64 )
from network import ( SetupLocalHost, Ngrok, ThreadedServerResponder )

import api as SDAPI

def prepare_decompressed_image( size : tuple, data : str ) -> Image.Image:
	color_pallete, encoded_pixels = zlib.decompress( bytes.fromhex(data) ).decode('utf-8').replace("'", '"').split('|')
	return decompress_image_complete(
		size,
		json.loads( color_pallete ),
		json.loads( encoded_pixels )
	)

if __name__ == '__main__':

	def get_operation_images( hash_id : str ) -> list:
		return [
			prepare_compressed_image( image )
			for image in SDAPI.get_images_from_operation( hash_id )
			if image != None
		]

	def get_stable_diffusion_info( ) -> dict:
		return {
			"system" : SDAPI.SYS_INFO,
			"hypernetworks" : SDAPI.get_hypernetworks(),
			"embeddings" : SDAPI.get_embeddings(),
			"vaes" : SDAPI.get_vaes(),
			"checkpoints" : SDAPI.get_checkpoints(),
			"loras" : SDAPI.get_loras(),
			"samplers" : SDAPI.get_samplers()
		}

	def txt2imgWrapper( data : dict ) -> str:
		data['log_file'] = 'img_cache/log.txt'
		return SDAPI.txt2img( **data )

	command_matrix = {
		"get_stable_diffusion_info" : lambda _, __ : get_stable_diffusion_info(),
		"get_operation_status" : lambda _, content : SDAPI.get_operation_status( content.get('data').get('hash') ),
		"get_operation_images" : lambda _, content : get_operation_images( content.get('data').get('hash') ),
		"txt_2_image" : lambda _, content : txt2imgWrapper( json.loads( zlib.decompress( bytes.fromhex( content.get('data') ) ) ) ),
	}

	def on_post( self : ThreadedServerResponder, content_length : int, content : str ) -> None:
		try:
			content = json.loads(content)
		except:
			return 400, json.dumps({"message": "invalid json"})

		command = content.get("command")
		if command == None:
			return 400, json.dumps({"message": "no command parameter"})

		response_message = json.dumps({"message": "unknown command"})

		callback = command_matrix.get(command)
		if callback != None:
			response_message = json.dumps({ "message" : callback( self, content ) })

		return 200, response_message

	print("Webserver Started")

	webserver = SetupLocalHost(port=500, onPOST=on_post)

	Ngrok.set_port(webserver.webserver.server_port)
	Ngrok.open_tunnel()

	print("Ngrok Public Address: ", Ngrok.get_ngrok_addr())
	print("In your SDAPI.lua, set the python server address to the above.")

	# response = requests.post('http://127.0.0.1:500', json={"command" : "get_sys_info"})
	# print(response.status_code, response.reason, response.json()["message"])

	while True:
		try:
			sleep(1/60)
		except KeyboardInterrupt:
			break
		except Exception:
			break

	Ngrok.close_tunnel()
	webserver.shutdown()

	print("Webserver Closed")
