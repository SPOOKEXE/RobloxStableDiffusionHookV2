
local HttpService = game:GetService('HttpService')

local ServerStorage = game:GetService('ServerStorage')
local StableDiffusionServer = require(ServerStorage:WaitForChild('SDServer'))

local ReplicatedStorage = game:GetService('ReplicatedStorage')
local StableDiffusionShared = require(ReplicatedStorage:WaitForChild('SDShared'))

-- test hosted caching of stable diffusion instances informations
local _, data = StableDiffusionServer.GetSDInstances()
print(data and HttpService:JSONEncode(data) or 'SD Unavailable')

--[[
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
]]

--[[]]
	local custom_hash_id = '2d6dc1f7a7a44c79a986751279befbf2'
	local _, image = StableDiffusionServer.GetHashImage(custom_hash_id)
	print(string.sub(image,1,100))


local RenderPart = Instance.new('Part')
RenderPart.Name = 'RenderPart'
RenderPart.CanCollide = false
RenderPart.CanTouch = false
RenderPart.CanQuery = false
RenderPart.Transparency = 1
RenderPart.Anchored = true
RenderPart.TopSurface = Enum.SurfaceType.Smooth
RenderPart.BottomSurface = Enum.SurfaceType.Smooth
RenderPart.Parent = workspace
local SurfaceGui = Instance.new('SurfaceGui')
SurfaceGui.Name = 'SurfaceGui'
SurfaceGui.Adornee = RenderPart
SurfaceGui.Brightness = 1
SurfaceGui.Face = Enum.NormalId.Front
SurfaceGui.MaxDistance = 100
SurfaceGui.ResetOnSpawn = false
SurfaceGui.PixelsPerStud = 256
SurfaceGui.SizingMode = Enum.SurfaceGuiSizingMode.PixelsPerStud
SurfaceGui.Parent = RenderPart

local PixelBoardFrame = StableDiffusionShared.PreparePixelBoard( SurfaceGui, 256, 256 )

local startTime = os.clock()
print('Decoding Pixels Start: 0')
local pixelBoard = StableDiffusionShared.DecodePixels( image )
print( pixelBoard )

print('Rendering Image Started: ', math.round((os.clock() - startTime) * 100) / 100)
local textBoard = StableDiffusionShared.PixelifyRow( pixelBoard, 256 )
print(textBoard)
StableDiffusionShared.DisplayTextForm( textBoard, PixelBoardFrame )
print( 'Rendering Image Completed: '.. tostring(math.round((os.clock() - startTime) * 100) / 100) )
