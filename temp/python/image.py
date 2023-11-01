
import numpy
import json

from PIL import Image, ImageEnhance

def round_pixels_to_nearest( pixels : list, round_n : int = 5 ) -> list:
	return [ [ [ round(r/round_n), round(g/round_n), round(b/round_n) ] for r,g,b in row ] for row in pixels ]

def greedy_fill_search( pixels : list, startIndex : int ) -> tuple:
	value = pixels[startIndex]
	count = 1
	while startIndex < len(pixels) - 1:
		startIndex += 1
		idx_value = pixels[ startIndex ]
		if value == idx_value:
			count += 1
		else:
			break
	return count, value

def get_frequent_colors( pixels : list, min_usage_count : int = 5 ) -> dict:
	temp_frequencies = []
	temp_pallete = { }

	# get frequencies of all the colors
	def parse_pixel( r : int, g : int, b : int ) -> None:
		nonlocal temp_frequencies, temp_pallete
		idx = f"{r},{g},{b}"
		if temp_frequencies[-1].get(idx):
			temp_frequencies[-1][idx] += 1
		else:
			temp_frequencies[-1][idx] = 1
			temp_pallete[idx] = [r,g,b]
	for row in pixels:
		temp_frequencies.append({})
		for r,g,b in row:
			parse_pixel( r, g, b )

	# find the minimum duplicates
	pallete = {}
	for d in temp_frequencies:
		frequencies = { }
		for k, v in d.items():
			if v < min_usage_count:
				continue
			frequencies[k] = v
			pallete[k] = temp_pallete[k]
	return pallete

def to_pallete_format( pixels : list, min_usage_count=3 ) -> tuple:
	pallete = get_frequent_colors( pixels, min_usage_count=3 )

	new_pixel_array = []
	pixel_pallete = []
	pallete_to_index = { }
	for index, column in enumerate(pixels):
		new_column = []
		idx = 0
		while idx < len(column):
			count, value = greedy_fill_search( column, idx )
			idx += count
			if count >= min_usage_count:
				cccc = f"{value[0]},{value[1]},{value[2]}"
				if not pallete_to_index.get( cccc ):
					pixel_pallete.append( pallete[cccc] )
					pallete_to_index[ cccc ] = len(pixel_pallete)
				new_column.append(f"{ count }y{ pallete_to_index[ cccc ] }")
			else:
				new_column.extend([value] * count)
		new_pixel_array.append( new_column )
	return pixel_pallete, new_pixel_array

def compress_image_complete( image : Image.Image, round_n : int = 5, min_usage_count : int = 3 ) -> tuple:
	dims, pixels = image.size, numpy.array(image).tolist()
	pallete, pixels = to_pallete_format(
		round_pixels_to_nearest( pixels, round_n=round_n ),
		min_usage_count=min_usage_count
	)
	return dims, pallete, pixels

def decompress_image_complete( dims : tuple, pallete : list, pixels : list ) -> Image.Image:
	# undo greedy fill
	new_pixels = []
	counter = 0
	for col in pixels:
		new_col = []
		for value in col:
			if type(value) != str:
				new_col.append(value)
				continue
			if value.find('y') != -1:
				count, pallete_index = value.split('y')
				count = int(count)
				counter += (count - 1)
				pallete_index = int(pallete_index) - 1
				rgb = pallete[pallete_index]
				for _ in range(count):
					new_col.append(rgb)
		new_pixels.append(new_col)

	# with open('dumpy.json', "w") as file:
	# 	file.write( json.dumps(new_pixels) )

	# load to image
	return Image.fromarray( numpy.array(new_pixels, dtype=numpy.uint8), mode='RGB')
