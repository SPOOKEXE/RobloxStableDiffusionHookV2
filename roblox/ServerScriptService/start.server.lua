
local HttpService = game:GetService('HttpService')

local ServerStorage = game:GetService('ServerStorage')
local StableDiffusionServer = require(ServerStorage:WaitForChild('SDServer'))

--[[
	local ReplicatedStorage = game:GetService('ReplicatedStorage')
	local StableDiffusionShared = require(ReplicatedStorage:WaitForChild('SDShared'))
]]

-- test hosted caching of stable diffusion instances informations
local _, data = StableDiffusionServer.GetSDInstances()
print(data and HttpService:JSONEncode(data) or 'SD Unavailable')

local image = StableDiffusionServer.AwaitText2Image(
	'SPOOK_EXE',

	'v1-5-pruned-emaonly.safetensors [6ce0161689]',
	{ },
	{ },
	{ },
	'pug',
	'',
	'Euler a',
	25,
	7,
	512,
	512,
	-1
)

print(#image)

--[[
	task.spawn(function()
		local _, _ = pcall(function()
			local image = SDServer.AwaitText2Image(...)

			local TargetScreenGui = workspace:WaitForChild('Part').SurfaceGui
			-- print('Preparing the template pixel board @ ', TargetScreenGui:GetFullName())
			local PixelBoardFrame = StableDiffusionShared.PixelBoardModule.PreparePixelBoard( TargetScreenGui )

			-- print('decoding pixels')
			local startTime = os.clock()
			local pixelBoard = StableDiffusionShared.DecodePixels( image )

			-- print('rendering image start')
			local textBoard = StableDiffusionShared.PixelBoardModule.ConvertPixelsToTextForm( pixelBoard )

			StableDiffusionShared.PixelBoardModule.DisplayTextForm( textBoard, PixelBoardFrame )
			print( 'The render operation took '.. tostring(math.round((os.clock() - startTime) * 100) / 100).. ' seconds to render on image labels.' )
		end)

		Module.BusyGeneratingPixels = false
	end)
]]

