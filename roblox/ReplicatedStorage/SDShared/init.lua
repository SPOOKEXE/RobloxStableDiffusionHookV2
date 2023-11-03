local HttpService = game:GetService("HttpService")

local Character = '█'
local basePixelText = '<font color="rgb(%s,%s,%s)">%s</font>'

local DEFAULT_WIDTH = 256

local TemplateGridFrame = Instance.new('Frame') do
	TemplateGridFrame.Name = 'Grid'
	TemplateGridFrame.BackgroundTransparency = 0
	TemplateGridFrame.BackgroundColor3 = Color3.new()
	TemplateGridFrame.AnchorPoint = Vector2.new(0.5, 0.5)
	TemplateGridFrame.Position = UDim2.fromScale(0.5, 0.5)
	TemplateGridFrame.ClipsDescendants = false
	TemplateGridFrame.Size = UDim2.fromScale(1, 1)
	local AspectRatio = Instance.new('UIAspectRatioConstraint')
	AspectRatio.AspectRatio = 1
	AspectRatio.AspectType = Enum.AspectType.ScaleWithParentSize
	AspectRatio.Parent = TemplateGridFrame
	local GridLayout = Instance.new('UIGridLayout')
	GridLayout.CellPadding = UDim2.fromOffset(0, -6)
	GridLayout.CellSize = UDim2.new(1, 0, 0, 24)
	GridLayout.HorizontalAlignment = Enum.HorizontalAlignment.Center
	GridLayout.VerticalAlignment = Enum.VerticalAlignment.Center
	GridLayout.SortOrder = Enum.SortOrder.LayoutOrder
	GridLayout.Parent = TemplateGridFrame
end

local TemplatePixelLabel = Instance.new('Frame') do
	TemplatePixelLabel.Name = 'TemplateFrame'
	TemplatePixelLabel.BackgroundTransparency = 1
	TemplatePixelLabel.Size = UDim2.new(1, 0, 0, 20)
	TemplatePixelLabel.ClipsDescendants = false
	local Label = Instance.new('TextLabel')
	Label.Name = 'Label'
	Label.BackgroundTransparency = 1
	Label.Size = UDim2.fromScale(1, 1)
	Label.FontFace = Font.new('rbxasset://fonts/families/SourceSansPro.json', Enum.FontWeight.Bold)
	Label.Text = ''
	Label.RichText = true
	Label.TextColor3 = Color3.new(1,1,1)
	Label.TextScaled = false
	Label.TextSize = 26
	--Label.TextWrapped = false
	Label.TextXAlignment = Enum.TextXAlignment.Center
	Label.TextYAlignment = Enum.TextYAlignment.Center
	Label.ClipsDescendants = false
	Label.Parent = TemplatePixelLabel
end

local function CreateRandomPixels(noPixels)
	local pixels = {}
	for _ = 1, noPixels do
		table.insert(pixels, { math.round(math.random(1,255)/5), math.round(math.random(1,255)/5), math.round(math.random(1,255)/5) })
	end
	return pixels
end

-- // Module // --
local Module = {}

Module.zlib = require(script.zlib)
Module.ActorPool = require(script.ActorPool)
Module.ActorPool.SetTargetActorAmount( 16 )

function Module.ToHex( value : string ) : string
	return value:gsub('.', function(c)
		return string.format('%02X', string.byte(c))
	end)
end

function Module.FromHex( value : string ) : string
	return value:gsub('..', function(cc)
		return string.char(tonumber(cc, 16))
	end)
end

-- Set size to 256x256 until PreparePixelBoard calculates the size needed
-- **TODO:** calculate size to fit pixels
function Module.PreparePixelBoard( surfaceGui : SurfaceGui, size_x : number?, size_y : number? ) : Frame
	size_x = size_x or DEFAULT_WIDTH
	size_y = size_y or DEFAULT_WIDTH
	local existantFrame = surfaceGui:FindFirstChildWhichIsA('Frame')
	if existantFrame then
		return existantFrame
	end

	surfaceGui.AlwaysOnTop = false
	surfaceGui.MaxDistance = 100

	local blackText = string.format(basePixelText, 0, 0, 0, string.rep(Character, size_x))
	local GridFrame = TemplateGridFrame:Clone()
	for index = 1, size_y do -- each row
		local Frame = TemplatePixelLabel:Clone()
		Frame.Name = index
		Frame.LayoutOrder = index
		Frame.Label.Text = blackText
		Frame.Parent = GridFrame
	end
	GridFrame.Parent = surfaceGui
	return GridFrame
end

function Module.DecodePixels( data : string ) : table
	return HttpService:JSONDecode( Module.zlib.Zlib.Decompress(data) )
end

function Module.PreprocessRowMatrix( pixels : table ) : table
	return Module.ActorPool.DistributeCalculation( 'DecodePixelRow', pixels, false, true )
end

function Module.DisplayTextForm( processedRows : table, gridFrame : Frame )
	for rowIndex, pixelText in ipairs( processedRows ) do
		local rowFrame = gridFrame:FindFirstChild(rowIndex)
		if rowFrame then
			rowFrame.Label.Text = pixelText
		end
	end
end

function Module.CreateRandomPixels( width : number, height : number ) : { table }
	local values = {}
	for _ = 1, width do
		table.insert(values, CreateRandomPixels(height))
	end
	return values
end

function Module.ClearPixelsOnBoard( frame : Frame, width : number? )
	width = width or DEFAULT_WIDTH

	local blankText = string.format(basePixelText, 0, 0, 0, string.rep(Character, width))
	for _, Frame in ipairs( frame:GetChildren() ) do
		if Frame:IsA('Frame') then
			Frame.Label.Text = blankText
		end
	end
end

function Module.ClearCurrentImage( TargetSurfaceGui : SurfaceGui, width : number?, height : number? )
	-- local TargetScreenGui = workspace:WaitForChild('Part').SurfaceGui
	local PixelBoardFrame = Module.PreparePixelBoard( TargetSurfaceGui, width, height )
	Module.ClearPixelsOnBoard( PixelBoardFrame, width )
end

return Module
