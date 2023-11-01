local HttpService = game:GetService("HttpService")

-- // Module // --
local Module = {}

Module.zlib = require(script.zlib)
Module.PixelBoardModule = require(script.pixelBoard)

Module.MinimumCommandInterval = 0
Module.CommandCooldowns = {
	Default = 0,

	Text2Image = 0,
	GetStableDiffusionInfo = 0,

	ClearCurrentImage = 0,
	--[[GetSystemInfo = 0,
	GetHyperNetworks = 0,
	GetEmbeddings = 0,
	GetVAEs = 0,
	GetCheckpoints = 0,
	GetLORAs = 0,
	GetSamplers = 0,
	GetUpscalers = 0,]]

	GetOperationStatus = 0,
	GetImagesFromOperationHash = 0,
	ClearCachedImage = 0,
}

Module.CommandEnums = {
	Text2Image = 0,

	ClearCurrentImage = 1,
	GetStableDiffusionInfo = 14,
	--[[GetSystemInfo = 1,
	GetHyperNetworks = 2,
	GetEmbeddings = 3,
	GetVAEs = 4,
	GetCheckpoints = 5,
	GetLORAs = 6,
	GetSamplers = 7,
	GetUpscalers = 8,]]

	GetOperationStatus = 15,
	GetImagesFromOperationHash = 16,
	ClearCachedImage = 17,
}

function Module.GetCommandNameFromValue( number : number ) : string?
	for commandName, commandValue in pairs( Module.CommandEnums ) do
		if commandValue == number then
			return commandName
		end
	end
	return nil
end

function Module.GetCommandCooldown( commandName : string ) : number
	return Module.CommandCooldowns[commandName] or Module.CommandCooldowns.Default
end

function Module.ConvertToRobloxBrackets( value : string ) : string
	return value:gsub("'", '"')
end

function Module.DecodePixels( data ) : table
	local decompressed = Module.zlib.Zlib.Decompress( Module.DecodeHex(data) )

	local ColorPallete, EncodedPixels = unpack(string.split( decompressed, '|' ))
	ColorPallete = HttpService:JSONDecode( Module.ConvertToRobloxBrackets(ColorPallete) )
	EncodedPixels = HttpService:JSONDecode( Module.ConvertToRobloxBrackets(EncodedPixels) )

	local pixels = {}
	for _, column in ipairs( EncodedPixels ) do
		local new_col = { }
		for _, value in ipairs( column ) do
			if typeof(value) ~= "string" then
				table.insert(new_col, value)
				continue
			end

			if not string.find(value, "y") then
				continue
			end

			local count, pallete_index = unpack(string.split(value, "y"))
			count = tonumber(count)
			pallete_index = tonumber(pallete_index)
			local rgb = ColorPallete[pallete_index]
			table.insert(new_col, count..'y'..HttpService:JSONEncode(rgb):gsub("%[", ""):gsub("%]", ""))
		end
		table.insert(pixels, new_col)
	end

	return pixels
end

function Module.EncodeHex(str)
	return (str:gsub('.', function (c)
		return string.format('%02X', string.byte(c))
	end))
end

function Module.DecodeHex(str)
	return (str:gsub('..', function (cc)
		return string.char(tonumber(cc, 16))
	end))
end

function Module.Text2ImageSugar( promptData : table ) : table?
	local ReplicatedStorage = game:GetService('ReplicatedStorage')
	local StableDiffusionFunction = ReplicatedStorage:WaitForChild('StableDiffusionFunction')

	local function InvokeStableDiffusion( command : number?, ... : any? ) : ...any?
		local compressed = Module.EncodeHex( Module.zlib.Zlib.Compress( HttpService:JSONEncode({ command, ... }) ) )
		local compressedReturn = StableDiffusionFunction:InvokeServer( compressed )
		local results = HttpService:JSONDecode(Module.zlib.Zlib.Decompress(Module.DecodeHex(compressedReturn)))
		table.remove(results, 1) -- success boolean
		return unpack(results)
	end

	print("Sending the prompt to stable diffusion and awaiting operation hash.")
	-- print( promptData )

	local hashId = InvokeStableDiffusion( Module.CommandEnums.Text2Image, unpack(promptData) )
	print( "Got Operation Hash: ", hashId )

	local StatusEnums = { ["-1" ] = "Failed", ["1"] = "Busy Generating", ["2"] = "Completed" }
	local status = InvokeStableDiffusion( Module.CommandEnums.GetOperationStatus, hashId )
	print(StatusEnums[tostring(status)] or "Unknown State")
	while status ~= -1 and status ~= 2 do
		task.wait(Module.CommandCooldowns.GetOperationStatus)
		status = InvokeStableDiffusion( Module.CommandEnums.GetOperationStatus, hashId )
		print(StatusEnums[tostring(status)] or "Unknown State")
	end

	if status ~= 2 then
		print('Failed to generate images.')
		return
	end

	print("Images successfully generated - downloading images.")
	return InvokeStableDiffusion( Module.CommandEnums.GetImagesFromOperationHash, hashId )[1]
end

return Module
