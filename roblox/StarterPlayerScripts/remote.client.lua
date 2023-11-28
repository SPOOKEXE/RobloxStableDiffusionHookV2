
local TextChatService = game:GetService('TextChatService')

local ReplicatedStorage = game:GetService('ReplicatedStorage')
local SDShared = require(ReplicatedStorage:WaitForChild('SDShared'))
local RemoteEnums = require(ReplicatedStorage:WaitForChild('RemoteEnums'))

local OperationStatus = RemoteEnums.OperationStatus

local SDRemoteFunction = ReplicatedStorage:WaitForChild('SDFunction')

local function InvokeServer( ... )
	return unpack(
		RemoteEnums.DecompressJSON(
			SDRemoteFunction:InvokeServer(
				RemoteEnums.CompressJSON( {...} )
			)
		)
	)
end

do
	local Success, SDInstances = InvokeServer( RemoteEnums.Commands.GetSDInstances )
	assert( Success, 'Failed to get the stable diffusion instances info.' )
	print( 'Avaialble SD Instances: ', #SDInstances )
end

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
local PixelBoardFrame = SDShared.PreparePixelBoard( SurfaceGui, IMG_SIZE, IMG_SIZE )

local function RenderImage( image )
	local startTime = os.clock()
	print('Decoding Pixels and Pixelify Started.')
	local pixelBoard = SDShared.DecodePixelsAndPixelify( image, IMG_SIZE )
	print( #pixelBoard )

	SDShared.DisplayTextForm( pixelBoard, PixelBoardFrame )
	print( 'Rendering Image Completed: '.. tostring(math.round((os.clock() - startTime) * 100) / 100) )
end

local function TrackHashId( hash : string )

	local _, status = InvokeServer(RemoteEnums.Commands.GetHashStatus, hash)
	print(status)

	assert( status ~= OperationStatus.Errored, 'Operation Errored! ' .. tostring(status) )

	while status == OperationStatus.InQueue do
		print( 'In Queue at Position: ' .. tostring(status) )
		local _, QueueLength = InvokeServer(RemoteEnums.Commands.GetHashQueue, hash)
		print( 'Queue Length: ', QueueLength)
		task.wait(1)
		_, status = InvokeServer(RemoteEnums.Commands.GetHashStatus, hash)
		print(status)
		assert( status ~= OperationStatus.Errored, 'Operation Errored! ' .. tostring(status) )
	end

	while status == OperationStatus.InProgress do
		local _, Progress = InvokeServer(RemoteEnums.Commands.GetHashProgress, hash)
		print('Currently generating: ', Progress)
		task.wait(1)
		_, status = InvokeServer(RemoteEnums.Commands.GetHashStatus, hash)
		print(status)
		assert( status ~= OperationStatus.Errored, 'Operation Errored! ' .. tostring(status) )
	end

	print('Grabbing Image.')
	local _, image = InvokeServer(RemoteEnums.Commands.GetHashImage, hash)
	print(#image)
	RenderImage( image )
end

local function RunPrompt( prompt, negative_prompt )
	print('Sending Prompt')

	local Prompt = {
		'v1-5-pruned.safetensors [1a189f0be6]',
		{},
		{},
		{},
		prompt,
		negative_prompt,
		'Euler a',
		25,
		7,
		512,
		512,
	}

	local Success, Hash = InvokeServer( RemoteEnums.Commands.Text2Image, unpack(Prompt) )
	assert( Success, 'Failed to generate image: ' .. tostring(Hash) )

	print( Hash )
	task.defer( TrackHashId, Hash )
end

TextChatService.SendingMessage:Connect(function(textChatMessage : TextChatMessage)
	local Splits = string.split(textChatMessage.Text, '|')
	if #Splits == 2 then
		RunPrompt( unpack(Splits) )
	end
end)
