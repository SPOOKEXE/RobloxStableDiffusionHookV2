
local HttpService = game:GetService('HttpService')

local ReplicatedStorage = game:GetService('ReplicatedStorage')
local StableDiffusionShared = require(ReplicatedStorage:WaitForChild('SDShared'))

--local PYTHON_SERVER_URL : string = 'https://b53592d35353.ngrok.app'
local PYTHON_SERVER_URL : string = 'http://127.0.0.1:500'

local function RequestAsync( url : string, body : any) : (boolean, (string | table)?)
	local response = nil
	local success, err = pcall(function()
		-- print("Requesting to ", Url, " with body ", Body)
		response = HttpService:RequestAsync({
			Url = url,
			Method = "POST",
			Headers = {
				["Content-Type"] = "application/json",
			},
			Body = HttpService:JSONEncode(body),
		})
	end)

	if not success then
		warn(err)
		return false, nil
	end

	local decodedBody = HttpService:JSONDecode(response.Body)
	if decodedBody['data'] then
		return success, unpack(HttpService:JSONDecode(StableDiffusionShared.zlib.Zlib.Decompress(
			StableDiffusionShared.FromHex( decodedBody['data'] )
		)))
	end
	return success, decodedBody['message']
end

local function typeAssert( param_name, value, ... )
	local isOfType = false
	for _, expected_type in ipairs( { ... } ) do
		if not isOfType then
			isOfType = typeof(value) == expected_type
		end
	end

	if not isOfType then
		error( string.format("%s must be of types: %s.", param_name, table.concat({...}, ' or ') ) )
	end
end

-- // Module // --
local Module = {}

function Module.GetSDInstances() : ( boolean, { table? } )
	return RequestAsync(PYTHON_SERVER_URL, { command = 'get_sd_instances', })
end

--[[
	Get the target operation hash's status.
]]
function Module.GetHashStatus( hash_id : string ) : (boolean, number?)
	typeAssert( 'hash_id', hash_id, 'string' )
	return RequestAsync(PYTHON_SERVER_URL, { command = 'get_hash_status', hash = hash_id })
end

--[[
	Get the target operation hash's queue if available.
]]
function Module.GetHashQueue( hash_id : string ) : (boolean, table?)
	typeAssert( 'hash_id', hash_id, 'string' )
	return RequestAsync(PYTHON_SERVER_URL, { command = 'get_hash_queue', hash = hash_id })
end

--[[
	Get the target operation hash's generation progress if available.
]]
function Module.GetHashProgress( hash_id : string ) : (boolean, table?)
	typeAssert( 'hash_id', hash_id, 'string' )
	return RequestAsync(PYTHON_SERVER_URL, { command = 'get_hash_progress', hash = hash_id })
end

--[[
	Get the target operation hash's generated image from the server if available.
]]
function Module.GetHashImage( hash_id : string ) : (boolean, string?)
	typeAssert( 'hash_id', hash_id, 'string' )
	return RequestAsync(PYTHON_SERVER_URL, {
		command = 'get_hash_image', hash = hash_id
	})
end

--[[
	POST a prompt to the stable diffusion distributor server.

	Returns a operation HASH_ID so the prompt can be kept track of externally.

	Optional parameters:
	- username : string
	- seed : number
	- [UNAVAILABLE] batch_count : number
	- [UNAVAILABLE] batch_size : number
]]
function Module.Text2Image(
	username : string?,
	userid : number?,

	checkpoint : string,
	textual_inversions : { table }, -- { name, weight }
	hypernetworks : { table }, -- { name, weight }
	loras : { table }, -- { name, weight }

	prompt : string,
	negative_prompt : string,

	sampling_method : string,
	steps : number,
	cfg_scale : number,
	width : number,
	height : number,

	-- batch_count : number?,
	-- batch_size : number?,
	seed : number?
) : (boolean, string?)

	typeAssert('username', username, 'string', 'nil')
	typeAssert('userid', userid, 'number', 'nil')
	typeAssert('checkpoint', checkpoint, 'string')
	typeAssert('textual_inversions', textual_inversions, 'table')
	typeAssert('hypernetworks', hypernetworks, 'table')
	typeAssert('loras', loras, 'table')
	typeAssert('prompt', prompt, 'string')
	typeAssert('negative_prompt', negative_prompt, 'string')
	typeAssert('sampling_method', sampling_method, 'string')
	typeAssert('steps', steps, 'number')
	typeAssert('cfg_scale', cfg_scale, 'number')
	typeAssert('width', width, 'number')
	typeAssert('height', height, 'number')
	-- typeAssert('batch_count', batch_count, 'number')
	-- typeAssert('batch_size', batch_size, 'number')
	typeAssert('seed', seed, 'number', 'nil')

	local HYPERNETWORK_BASE = '<hypernetwork:%s:%s>'
	local LORA_BASE = '<lora:%s:%s>'
	local WEIGHTED_TEXT_BASE = '(%s:%s)'

	-- textual inversions
	local inversions = {}
	for _, inversion in ipairs( textual_inversions ) do
		table.insert( inversions, string.format(WEIGHTED_TEXT_BASE, unpack(inversion)) )
	end
	negative_prompt = negative_prompt .. " " .. table.concat(inversions, ' ')

	-- loras & hypernetworks
	local loras_text = { }
	for _, hyper in ipairs( hypernetworks ) do
		table.insert(loras_text, string.format(HYPERNETWORK_BASE, unpack(hyper)))
	end
	for _, lora in ipairs( loras ) do
		table.insert(loras_text, string.format(LORA_BASE, unpack(lora)))
	end
	prompt = prompt .. " " .. table.concat(loras_text, ' ')

	-- construction of prompt
	local ConstructedPrompt = {
		username = username,
		userid = userid,

		checkpoint = checkpoint,

		prompt = prompt,
		negative_prompt = negative_prompt,
		steps = steps,
		cfg_scale = cfg_scale,
		sampler_name = sampling_method,

		width = width,
		height = height,
		seed = seed,

		--batch_size = batch_size,
		--batch_count = batch_count,
	}

	-- prompt compression
	local compressedPrompt = StableDiffusionShared.ToHex(
		StableDiffusionShared.zlib.Zlib.Compress(
			HttpService:JSONEncode(ConstructedPrompt)
		)
	)

	-- POST to server
	return RequestAsync( PYTHON_SERVER_URL, {
		command = "post_txt2img",
		prompt = compressedPrompt,
		forceIndex = nil, -- force a specific server index (e.g. VIP server)
	})
end

--[[
	POST a prompt to the stable diffusion distributor server.

	Returns the resultant image or nil if the operation failed.

	Optional parameters:
	- username : string
	- seed : number
	- [UNAVAILABLE] batch_count : number
	- [UNAVAILABLE] batch_size : number

	This awaits for the FULL completion of the image creation and returns the image data if successful or nil if not.
]]
function Module.AwaitText2Image(
	username : string?,
	userid : number?,
	checkpoint : string,
	textual_inversions : { table }, -- { name, weight }
	hypernetworks : { table }, -- { name, weight }
	loras : { table }, -- { name, weight }
	prompt : string,
	negative_prompt : string,
	sampling_method : string,
	steps : number,
	cfg_scale : number,
	width : number,
	height : number,
	-- batch_count : number,
	-- batch_size : number,
	seed : number
) : string?

	local success, hashId = Module.Text2Image(
		username,
		userid,
		checkpoint,
		textual_inversions, -- { name, weight }
		hypernetworks, -- { name, weight }
		loras, -- { name, weight }

		prompt,
		negative_prompt,

		sampling_method,
		steps,
		cfg_scale,
		width,
		height,

		-- batch_count,
		-- batch_size,
		seed
	)

	assert( success, 'Could not POST prompt to server: ' .. tostring(hashId) )

	Module.HashStatusEnum = {
		NonExistent = -1,
		InQueue = 0,
		InProgress = 1,
		Finished = 2,
		Errored = 3,
	}

	print( hashId )
	local StatusEnums = {
		['-1'] = "Failed",
		['0'] = 'In Queue',
		['1'] = "Generating",
		['2'] = "Completed",
		['3'] = 'Errored'
	}

	local _, status = Module.GetHashStatus( hashId )
	print(StatusEnums[tostring(status)] or "Unknown State")

	local endStates = { StableDiffusionShared.HashStatusEnum.NonExistent, StableDiffusionShared.HashStatusEnum.Finished, StableDiffusionShared.HashStatusEnum.Errored }
	while not table.find(endStates, status) do
		task.wait(1)
		_, status = Module.GetHashStatus( hashId )
		print(StatusEnums[tostring(status)] or "Unknown State")
		if status == StableDiffusionShared.HashStatusEnum.InQueue then
			local _, Data = Module.GetHashQueue(hashId)
			print( Data )
		elseif status == StableDiffusionShared.HashStatusEnum.InProgress then
			local _, Data = Module.GetHashProgress(hashId)
			print( Data )
		end
	end

	local _, image = nil, nil
	if status == 2 then
		_, image = Module.GetHashImage( hashId )
	end
	return image
end

return Module
