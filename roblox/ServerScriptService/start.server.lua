
local HttpService = game:GetService('HttpService')

local ServerStorage = game:GetService('ServerStorage')
local StableDiffusionServer = require(ServerStorage:WaitForChild('SDServer'))

local ReplicatedStorage = game:GetService('ReplicatedStorage')
local StableDiffusionShared = require(ReplicatedStorage:WaitForChild('SDShared'))

-- test hosted caching of stable diffusion instances informations
local _, data = StableDiffusionServer.GetSDInstances()
print(data and HttpService:JSONEncode(data) or 'SD Unavailable')

--[[]]
local image = StableDiffusionServer.AwaitText2Image(
	'SPOOK_EXE',

	'v1-5-pruned-emaonly.safetensors [6ce0161689]',
	{ },
	{ },
	{ },
	'waterfall landscape',
	'',
	'Euler a',
	25,
	7,
	1024,
	512,
	-1
)

--[[
	local custom_hash_id = '200dfae229e14cf1b7dab4421fab2a33'
	local _, image = StableDiffusionServer.GetHashImage(custom_hash_id)
	print(string.sub(image,1,100))
]]

local RenderPart = Instance.new('Part')
RenderPart.Name = 'RenderPart'
RenderPart.CanCollide = false
RenderPart.CanTouch = false
RenderPart.Color = Color3.new(0, 0, 0)
RenderPart.CanQuery = false
RenderPart.Transparency = 0
RenderPart.Anchored = true
RenderPart.TopSurface = Enum.SurfaceType.Smooth
RenderPart.BottomSurface = Enum.SurfaceType.Smooth
RenderPart.Size = Vector3.new(18, 18, 1)
RenderPart.Position = Vector3.new(0, 9, 0)
RenderPart.Parent = workspace
local SurfaceGui = Instance.new('SurfaceGui')
SurfaceGui.Name = 'SurfaceGui'
SurfaceGui.AlwaysOnTop = true
SurfaceGui.Adornee = RenderPart
SurfaceGui.Brightness = 1
SurfaceGui.Face = Enum.NormalId.Front
SurfaceGui.MaxDistance = 100
SurfaceGui.ResetOnSpawn = false
SurfaceGui.PixelsPerStud = 256
SurfaceGui.SizingMode = Enum.SurfaceGuiSizingMode.PixelsPerStud
SurfaceGui.Parent = RenderPart

local IMG_SIZE = 256

local PixelBoardFrame = StableDiffusionShared.PreparePixelBoard( SurfaceGui, IMG_SIZE, IMG_SIZE )

local startTime = os.clock()
print('Decoding Pixels and Pixelify Started.')
local pixelBoard = StableDiffusionShared.DecodePixelsAndPixelify( image, IMG_SIZE )
print( #pixelBoard )

StableDiffusionShared.DisplayTextForm( pixelBoard, PixelBoardFrame )
print( 'Rendering Image Completed: '.. tostring(math.round((os.clock() - startTime) * 100) / 100) )
