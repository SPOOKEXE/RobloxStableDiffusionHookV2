
import numpy
import json

from PIL import Image, ImageEnhance

def round_pixels_to_nearest( pixels : list, round_n : int = 5 ) -> list:
	return [ [ [ round(r/round_n), round(g/round_n), round(b/round_n) ] for r,g,b in row ] for row in pixels ]

def greedy_fill_search( pixels : list, startIndex : int ) -> tuple:
	value : list = pixels[startIndex]
	count : int = 1
	while startIndex < len(pixels) - 1:
		startIndex += 1
		idx_value : list = pixels[ startIndex ]
		if value == idx_value:
			count += 1
		else:
			break
	return count, value

def get_frequent_colors( pixels : list, min_usage_count : int = 5 ) -> dict:
	temp_frequencies = []
	temp_pallete = { }

	# get frequencies of all the colors
	for row in pixels:
		row_dict = { }
		for r,g,b in row:
			idx = f"{r},{g},{b}"
			if row_dict.get(idx) != None:
				row_dict[idx] += 1
			else:
				row_dict[idx] = 1
				temp_pallete[idx] = [r,g,b]
		temp_frequencies.append(row_dict)

	# find the minimum duplicates
	pallete : dict = {}
	for d in temp_frequencies:
		frequencies = { }
		for k, v in d.items():
			if v < min_usage_count:
				continue
			frequencies[k] = v
			pallete[k] = temp_pallete[k]

	return pallete

def to_pallete_format( pixels : list, min_usage_count : int = 3 ) -> tuple:
	pallete = get_frequent_colors( pixels, min_usage_count=3 )

	new_pixel_array = []
	pixel_pallete = []
	pallete_to_index = { }
	for column in pixels:
		new_column = []
		counter = 0
		while counter < len(column):
			count, value = greedy_fill_search( column, counter )
			counter += count
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
	pallete, pixels = to_pallete_format( round_pixels_to_nearest( pixels, round_n=round_n ),min_usage_count=min_usage_count )
	return dims, pallete, pixels
