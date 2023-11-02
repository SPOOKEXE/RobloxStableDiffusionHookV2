
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
