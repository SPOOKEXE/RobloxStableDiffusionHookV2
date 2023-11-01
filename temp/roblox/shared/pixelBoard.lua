
local Character = '█'
local BasePixelText = '<font color="rgb(%s,%s,%s)">%s</font>'

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

function Module.PreparePixelBoard( surfaceGui )
	local existantFrame = surfaceGui:FindFirstChildWhichIsA('Frame')
	if existantFrame then
		return existantFrame
	end

	surfaceGui.AlwaysOnTop = false
	surfaceGui.MaxDistance = 100
	local GridFrame = TemplateGridFrame:Clone()
	for index = 1, 256 do
		local Frame = TemplatePixelLabel:Clone()
		Frame.Name = index
		Frame.LayoutOrder = index
		Frame.Label.Text = string.format(BasePixelText, 0, 0, 0, string.rep(Character, 256))
		Frame.Parent = GridFrame
	end
	GridFrame.Parent = surfaceGui
	return GridFrame
end

function Module.ConvertPixelsToTextForm( pixels )
	-- generate all independants
	local pixelBoard = { }
	for _, rowPixel in ipairs( pixels ) do

		-- fill in colors
		local rowPixels = { }
		local currentCharacterCount = 0
		for _, value in ipairs( rowPixel ) do
			if typeof(value) == "string" then
				-- compressed value unpack
				local count, rgb = unpack(string.split(value, 'y'))
				count = tonumber(count)
				currentCharacterCount += count
				local r,g,b = unpack(string.split(rgb,','))
				table.insert(rowPixels, string.format(BasePixelText, tonumber(r) * 5, tonumber(g) * 5, tonumber(b) * 5, string.rep(Character, count)))
			else
				-- individual pixel
				local text = string.format(BasePixelText, value[1] * 5, value[2] * 5, value[3] * 5, Character)
				table.insert(rowPixels, text)
				currentCharacterCount += 1
			end
		end

		-- fill in blanks with black (center image by putting 1 pixel on the left and right)
		if currentCharacterCount < 256 then
			local blackPixel = string.format(BasePixelText, 0,0,0, Character)
			local remainingAmount = (256 - currentCharacterCount)
			for _ = 1, math.floor(remainingAmount / 2) do
				table.insert(rowPixels, blackPixel)
				table.insert(rowPixels, 1, blackPixel)
			end
			-- if its an odd number, padd on the far right
			if remainingAmount % 2 == 1 then
				table.insert(rowPixels, blackPixel)
			end
		end

		-- insert to table after joining pixels together
		table.insert(pixelBoard, table.concat(rowPixels, ''))
	end

	-- TODO: if #pixels < 256, fill in top with half and bottom with half to pad it to center

	return pixelBoard

end

function Module.DisplayTextForm( textPixels : table, GridFrame : Frame )
	for rowIndex, pixelText in ipairs( textPixels ) do
		local rowFrame = GridFrame:FindFirstChild(rowIndex)
		if not rowFrame then
			continue
		end
		rowFrame.Label.Text = pixelText
	end
end

function Module.CreateRandomPixels( width, height )
	local pixelBoard = {}
	for _ = 1, width do
		table.insert(pixelBoard, CreateRandomPixels(height))
	end
	return pixelBoard
end

function Module.ClearPixelsOnBoard( GridFrame : Frame, width : number? )
	width = width or 256
	for _, Frame in ipairs( GridFrame:GetChildren() ) do
		if Frame:IsA('Frame') then
			Frame.Label.Text = string.format(BasePixelText, 0, 0, 0, string.rep(Character, width))
		end
	end
end

return Module
