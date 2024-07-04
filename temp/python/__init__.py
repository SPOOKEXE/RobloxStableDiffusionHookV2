
import traceback
import numpy
import zlib
import json

from image import compress_image_complete, load_image_from_sd

from PIL import Image
from typing import Any
from time import sleep

def compress_str_transmission( value : str ) -> str:
	return zlib.compress( bytes( value.strip(), encoding='utf-8' ), level=9 ).hex()

def decompress_json_transmission( value : str ) -> dict:
	return json.loads( zlib.decompress( bytes.fromhex( value ) ) )

def prepare_compressed_image( image_raw : str, image_size : tuple = (256,256) ) -> tuple:
	# load to image and reduce size
	image : Image.Image = load_image_from_sd( image_raw )
	image.thumbnail(image_size)
	# compress image
	print( 'Preparing compressed image:', image.size, len(str( numpy.array(image).tolist() ).replace(' ', '')) )
	size, color_pallete, encoded_pixels = compress_image_complete( image, round_n=5, min_usage_count=3 )
	return size, compress_str_transmission( (str(color_pallete) + "|" + str(encoded_pixels)).replace(' ', '') )
