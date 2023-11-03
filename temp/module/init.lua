
-- // Module // --
local Module = {}

Module.PythonServerURL = NGROK_URL
Module.ImageCache = { }

Module.CachedStableDiffusionInfo = nil
Module.LastStableDiffusionInfoUpdate = nil

function Module.GetStableDiffusionInfo()
	if Module.CachedStableDiffusionInfo and time() < Module.LastStableDiffusionInfoUpdate then
		return Module.CachedStableDiffusionInfo
	end
	Module.LastStableDiffusionInfoUpdate = time() + STABLE_DIFFUSION_INFO_UPDATE_INTERVAL

	Module.CachedStableDiffusionInfo = RequestAsync( Module.PythonServerURL, {
		command = "get_stable_diffusion_info",
	})

	return Module.CachedStableDiffusionInfo
end

function Module.ClearAllCachedImages()
	-- Module.ImageCache = { }
	Module.ImageCache = nil
end

function Module.CheckForExpiredImages( )
	--[[for hash, data in pairs( Module.ImageCache ) do
		if time() > data.Time then
			Module.ImageCache[hash] = nil
		end
	end]]
end

function Module.ClearCachedImage( hash : string )
	--Module.ImageCache[hash] = nil
	Module.ImageCache = nil
end

function Module.GetOperationStatus( hash : string ) : number
	local response = RequestAsync( Module.PythonServerURL, {
		command = "get_operation_status",
		data = { hash = hash, }
	})
	return response and response.status or -1
end

function Module.GetImagesFromOperationHash( hash : string )
	assert( typeof(hash) == "string", "Hash must be a string." )

	-- exists and can be returned
	if Module.ImageCache[hash] then
		-- print('cached')
		return Module.ImageCache[hash].Data
	end

	-- check if image is available
	if Module.GetOperationStatus( hash ) ~= 2 then
		-- print('operation not finished')
		return nil
	end

	print('Downloading image from python.')
	local imageArray = RequestAsync( Module.PythonServerURL, {
		command = "get_operation_images",
		data = {
			hash = hash,
		}
	})

	Module.ImageCache = imageArray

	--[[
	Module.ImageCache[hash] = {
		Time = time() + IMAGE_EXPIRY_TIME,
		Data = imageArray
	}
	]]

	return imageArray
end

function Module.ClearCurrentImage()
	local TargetScreenGui = workspace:WaitForChild('Part').SurfaceGui
	local PixelBoardFrame = StableDiffusionShared.PixelBoardModule.PreparePixelBoard( TargetScreenGui )

	StableDiffusionShared.PixelBoardModule.ClearPixelsOnBoard( PixelBoardFrame )
end

function Module.Text2Image(
	playerName : string,
	checkpoint : string,
	checkpoint_vae : string?,

	prompt : string,
	negative_prompt : string?,
	steps : number,
	cfg_scale : number,
	sampler_name : string,

	width : number,
	height : number,

	batch_size : number,
	batch_count : number,
	seed : number?
) : any?
	-- assertions
	typeAssert( "Checkpoint", checkpoint, "string" )
	typeAssert( "VAE", checkpoint_vae, "string", "nil" )

	typeAssert( "Prompt", prompt, "string" )
	typeAssert( "Negative Prompt", negative_prompt, "string", "nil" )
	typeAssert( "Steps", steps, "number" )
	typeAssert( "CFG Scale", cfg_scale, "number" )
	typeAssert( "Sampler", sampler_name, "string" )

	typeAssert( "Width", width, "number" )
	typeAssert( "Height", height, "number" )

	typeAssert( "Batch Size", batch_size, "number" )
	typeAssert( "Batch Count", batch_count, "number" )
	typeAssert( "Seed", seed, "number", "nil" )

	local compressedData = StableDiffusionShared.EncodeHex( StableDiffusionShared.zlib.Zlib.Compress( HttpService:JSONEncode({
		playerName = playerName,
		checkpoint = checkpoint,
		checkpoint_vae = checkpoint_vae,
		prompt = prompt,
		negative_prompt = negative_prompt,
		steps = steps,
		cfg_scale = cfg_scale,
		sampler_name = sampler_name,
		width = width,
		height = height,
		batch_size = batch_size,
		batch_count = batch_count,
		seed = seed,
	})))

	local hashId = RequestAsync( Module.PythonServerURL, {
		command = "txt_2_image",
		data = compressedData,
	})

	task.spawn(function()

		local _, _ = pcall(function()
			local StatusEnums = { ["-1" ] = "Failed", ["1"] = "Busy Generating", ["2"] = "Completed" }
			local status = Module.GetOperationStatus( hashId )
			print( StatusEnums[tostring(status)] or "Unknown State" )
			while status ~= -1 and status ~= 2 do
				task.wait(2)
				status = Module.GetOperationStatus( hashId )
				print(StatusEnums[tostring(status)] or "Unknown State")
			end
			local images = status == 2 and Module.GetImagesFromOperationHash( hashId )

			local TargetScreenGui = workspace:WaitForChild('Part').SurfaceGui
			-- print('Preparing the template pixel board @ ', TargetScreenGui:GetFullName())
			local PixelBoardFrame = StableDiffusionShared.PixelBoardModule.PreparePixelBoard( TargetScreenGui )

			-- print('decoding pixels')
			local startTime = os.clock()
			local pixelBoard = StableDiffusionShared.DecodePixels( images[1][2] )

			-- print('rendering image start')
			local textBoard = StableDiffusionShared.PixelBoardModule.ConvertPixelsToTextForm( pixelBoard )

			StableDiffusionShared.PixelBoardModule.DisplayTextForm( textBoard, PixelBoardFrame )
			print( 'The render operation took '.. tostring(math.round((os.clock() - startTime) * 100) / 100).. ' seconds to render on image labels.' )
		end)

		Module.BusyGeneratingPixels = false
	end)

	return hashId
end

function Module.AwaitTxt2ImageSugar( ... ) : table
	local hashId = Module.Text2Image( ... )
	print( hashId )
	local StatusEnums = { ["-1" ] = "Failed", ["1"] = "Busy Generating", ["2"] = "Completed" }
	local status = Module.GetOperationStatus( hashId )
	print(StatusEnums[tostring(status)] or "Unknown State")
	while status ~= -1 and status ~= 2 do
		task.wait(1)
		status = Module.GetOperationStatus( hashId )
		print(StatusEnums[tostring(status)] or "Unknown State")
	end
	return status == 2 and Module.GetImagesFromOperationHash( hashId )
end

return Module
