
local HttpService = game:GetService('HttpService')
local Players = game:GetService('Players')

local ServerStorage = game:GetService('ServerStorage')
local StableDiffusionAPI = require(ServerStorage:WaitForChild('StableDiffusionModule'))

local ReplicatedStorage = game:GetService('ReplicatedStorage')
local StableDiffusionShared = require(ReplicatedStorage:WaitForChild('StableDiffusionShared'))

local StableDiffusionFunction = ReplicatedStorage:FindFirstChild('StableDiffusionFunction')
if not StableDiffusionFunction then
	StableDiffusionFunction = Instance.new('RemoteFunction')
	StableDiffusionFunction.Name = 'StableDiffusionFunction'
	StableDiffusionFunction.Parent = ReplicatedStorage
end

--[[
	print('Preparing Pixel Board')
	local Frame = StableDiffusionShared.PixelBoardModule.PreparePixelBoard( workspace.Part.SurfaceGui )

	print('Requesting')
	local images = StableDiffusionAPI.AwaitTxt2ImageSugar(
		"v1-5-pruned-emaonly.safetensors [6ce0161689]",
		nil,
		"pug",
		"",
		25,
		7,
		"Euler a",
		512,
		512,
		1,
		1,
		nil
	)

	print('decoding pixels')
	local pixelBoard = StableDiffusionShared.DecodePixels( images[1][2] )

	print('rendering image start')
	local startTime = os.clock()
	local textBoard = StableDiffusionShared.PixelBoardModule.ConvertPixelsToTextForm( pixelBoard )

	StableDiffusionShared.PixelBoardModule.DisplayTextForm( textBoard, Frame )
	print( 'The operation took '.. tostring(os.clock() - startTime).. ' seconds to render on image labels.' )
]]

local CommandDebounces = {}
local CommandDebounceCache = { }

local function doCompression( value )
	return StableDiffusionShared.EncodeHex( StableDiffusionShared.zlib.Zlib.Compress( HttpService:JSONEncode( value ) ) )
end

StableDiffusionFunction.OnServerInvoke = function(LocalPlayer, compressed)
	local args = HttpService:JSONDecode(StableDiffusionShared.zlib.Zlib.Decompress( StableDiffusionShared.DecodeHex(compressed)  ))
	local command = table.remove(args, 1)

	local debounceTime = CommandDebounces[ LocalPlayer ]
	if debounceTime and time() < debounceTime then
		return doCompression({false, 'You are on global cooldown. Time remaining: ' .. tostring( math.floor( debounceTime - time() ) )})
	end
	CommandDebounces[ LocalPlayer ] = time() + StableDiffusionShared.MinimumCommandInterval -- prevent spam for ALL commands

	if not CommandDebounceCache[ LocalPlayer ] then
		CommandDebounceCache[ LocalPlayer ] = { }
	end

	assert( typeof(command) == "number" and math.fmod(command, 1) == 0, "Command must be an integer." )
	local commandName = StableDiffusionShared.GetCommandNameFromValue( command )
	assert( commandName ~= nil, "Invalid command value." )

	debounceTime = CommandDebounceCache[ LocalPlayer ][ command ]
	if debounceTime and time() < debounceTime then
		return doCompression({false, 'This command is on cooldown. Time remaining: ' .. tostring( math.floor( debounceTime - time() ) )})
	end

	local DebounceDuration = StableDiffusionShared.GetCommandCooldown( commandName )
	CommandDebounceCache[ LocalPlayer ][ command ] = time() + DebounceDuration

	local targetFunction = StableDiffusionAPI[ commandName ]
	if not targetFunction then
		return doCompression({false, 'Cannot find the command function.'})
	end

	if commandName == 'Text2Image' then
		if StableDiffusionAPI.BusyGeneratingPixels then
			return doCompression({false, 'Text2Image is currently busy generating another image.'})
		end
		StableDiffusionAPI.BusyGeneratingPixels = true
		table.insert( args, 1, LocalPlayer.Name )
	end

	local results = {pcall(targetFunction, unpack(args))}
	return doCompression(results)
end

Players.PlayerRemoving:Connect(function( LocalPlayer )
	CommandDebounceCache[ LocalPlayer ] = nil
end)
