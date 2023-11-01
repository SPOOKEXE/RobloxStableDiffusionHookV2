
local HttpService = game:GetService('HttpService')
local UserInputService = game:GetService('UserInputService')

local ReplicatedStorage = game:GetService('ReplicatedStorage')
local StableDiffusionShared = require(ReplicatedStorage:WaitForChild('StableDiffusionShared'))

local StableDiffusionFunction = ReplicatedStorage:WaitForChild('StableDiffusionFunction') :: RemoteFunction

local LocalPlayer = game:GetService('Players').LocalPlayer

local UIFolder = script.Parent:WaitForChild('UIFolder')

local DiffusionUI = UIFolder:WaitForChild('DiffusionUI')
DiffusionUI.Parent = LocalPlayer:WaitForChild('PlayerGui')

local CurrentStableDiffusionInfo = nil

local function InvokeStableDiffusion( command : number?, ... : any? ) : ...any?
	local arguments = { command, ... }
	arguments = StableDiffusionShared.EncodeHex( StableDiffusionShared.zlib.Zlib.Compress( HttpService:JSONEncode(arguments) ) )
	local compressedResult = StableDiffusionFunction:InvokeServer( arguments )
	local results = HttpService:JSONDecode( StableDiffusionShared.zlib.Zlib.Decompress( StableDiffusionShared.DecodeHex( compressedResult ) ) )
	table.remove(results, 1) -- success boolean
	return unpack(results)
end

local TargetScreenGui = workspace:WaitForChild('Part').SurfaceGui
print('Preparing the template pixel board @ ', TargetScreenGui:GetFullName())
-- local PixelBoardFrame = StableDiffusionShared.PixelBoardModule.PreparePixelBoard( TargetScreenGui )
print('Pixel board has been prepared.')

DiffusionUI.Enabled = false
UserInputService.InputBegan:Connect(function(inputObject, wasProcessed)
	if inputObject.KeyCode == Enum.KeyCode.P and not wasProcessed then
		DiffusionUI.Enabled = not DiffusionUI.Enabled
	elseif inputObject.KeyCode == Enum.KeyCode.BackSlash then
		InvokeStableDiffusion( StableDiffusionShared.CommandEnums.ClearCurrentImage )
	end
end)

DiffusionUI.Live.Visible = false

-- set default values here as well
local selectedInformation = {
	checkpoint = nil,
	vae = nil,
	samplers = 'Euler a',
	embeddings = { },
	loras = { },
	hypernetworks = { },
}

local selectedColor3 = Color3.fromRGB(68, 255, 0)
local notSelectedColor3 = Color3.new( 1, 1, 1 )

local function toCharByteString( str )
	local bytes = {}
	for _, char in string.split(str, '') do
		table.insert(bytes, string.byte(char))
	end
	return table.concat(bytes, ',')
end

local function OnSelectedInfoChanged()
	-- print( HttpService:JSONEncode(selectedInformation))

	local ModelsScrollFrame = DiffusionUI.Options.Frame.Menus.Models.Scroll.ModelsScroll
	for _, Frame in ipairs( ModelsScrollFrame:GetChildren() ) do
		if Frame:IsA('Frame') then
			local isSelected = selectedInformation.checkpoint and string.find(toCharByteString(Frame.Name), toCharByteString(selectedInformation.checkpoint))
			Frame.Label.TextColor3 = isSelected and selectedColor3 or notSelectedColor3
		end
	end

	local VAEsScrollFrame = DiffusionUI.Options.Frame.Menus.Models.Scroll.VAEScroll
	for _, Frame in ipairs( VAEsScrollFrame:GetChildren() ) do
		if Frame:IsA('Frame') then
			local isSelected = selectedInformation.vae and string.find(toCharByteString(Frame.Name), toCharByteString(selectedInformation.vae))
			Frame.Label.TextColor3 = isSelected and Color3.fromRGB(68, 255, 0) or Color3.new(1, 1, 1)
		end
	end

	local categoryNames = { 'samplers', 'hypernetworks', 'loras' }
	for _, categoryName in ipairs( categoryNames ) do
		local categoryFrame = DiffusionUI.Options.Frame.Menus.LORAs.Scroll:FindFirstChild( categoryName..'Scroll' )
		if not categoryFrame then
			continue
		end
		local selectedValue = selectedInformation[categoryName]
		for _, itemFrame in ipairs( categoryFrame:GetChildren() ) do
			if itemFrame:IsA("Frame") then
				local indexValue = itemFrame:GetAttribute('index')
				if not indexValue then
					continue
				end
				local isSelected = selectedValue and (typeof( selectedValue ) ~= "string" and table.find( selectedValue, indexValue ) or (selectedValue == indexValue))
				itemFrame.Label.TextColor3 = isSelected and selectedColor3 or notSelectedColor3
			end
		end
	end

	local EmbeddingScroll = DiffusionUI.Options.Frame.Menus.LORAs.Scroll:FindFirstChild('EmbeddingsScroll')
	if EmbeddingScroll then
		for _, embedderFrame in ipairs( EmbeddingScroll:GetChildren() ) do
			if embedderFrame:IsA('Frame') then
				local idx = embedderFrame:GetAttribute('index') or embedderFrame.Name
				local isSelected = selectedInformation.embeddings and table.find( selectedInformation.embeddings, idx )
				embedderFrame.Label.TextColor3 = isSelected and selectedColor3 or notSelectedColor3
			end
		end
	end
end

local function UpdateStableDiffusionUIInfo()
	if not CurrentStableDiffusionInfo then
		return
	end

	-- print( CurrentStableDiffusionInfo)

	local hasSelectedInfoChanged = false

	-- remove values we don't want
	CurrentStableDiffusionInfo.system.CPU.model = nil
	CurrentStableDiffusionInfo.system.Path = nil
	CurrentStableDiffusionInfo.system.RAM.free = nil

	for _, frame in ipairs( DiffusionUI.Options.Frame.Menus.Info.Scroll:GetChildren() ) do
		if frame:IsA('Frame') then
			frame:Destroy()
		end
	end

	-- system information
	local indexCounter = 0
	for categoryName, data in pairs( CurrentStableDiffusionInfo.system ) do

		local categoryDivider = UIFolder.TemplateDivider:Clone()
		categoryDivider.Name = categoryName
		categoryDivider.Label.Text = string.upper(categoryName)
		categoryDivider.LayoutOrder = indexCounter
		categoryDivider.Parent = DiffusionUI.Options.Frame.Menus.Info.Scroll

		for index, value in pairs( data ) do
			local labelName = categoryName .. '_' .. index

			local textLabel =  UIFolder.TemplateOption:Clone()
			textLabel.Button.Visible = false
			textLabel.Name = labelName
			textLabel.LayoutOrder = indexCounter
			if #data > 0 then
				textLabel.Label.Text = tostring(value)
			else
				local text = tostring(index) .. ': ' .. tostring(value)
				textLabel.Label.Text = text
			end

			indexCounter += 1
			textLabel.Parent = DiffusionUI.Options.Frame.Menus.Info.Scroll
		end

		indexCounter += 1
	end

	-- checkpoints & vaes
	DiffusionUI.Options.Frame.Menus.Models.Scroll.TopBuffer.LayoutOrder = 1
	DiffusionUI.Options.Frame.Menus.Models.Scroll.ModelsDivider.LayoutOrder = 2
	DiffusionUI.Options.Frame.Menus.Models.Scroll.ModelsScroll.LayoutOrder = 3
	DiffusionUI.Options.Frame.Menus.Models.Scroll.VAEDivider.LayoutOrder = 4
	DiffusionUI.Options.Frame.Menus.Models.Scroll.VAEScroll.LayoutOrder = 5
	DiffusionUI.Options.Frame.Menus.Models.Scroll.BottomBuffer.LayoutOrder = 6

	local CheckpointScrollFrame = DiffusionUI.Options.Frame.Menus.Models.Scroll.ModelsScroll
	local activeCheckpointNames = { }
	local activeCheckpointTitles = {}
	for index, checkpointData in ipairs( CurrentStableDiffusionInfo.checkpoints ) do
		local frameName = checkpointData['title']..'_'..checkpointData['size_bytes']
		table.insert(activeCheckpointNames, frameName)
		table.insert(activeCheckpointTitles, checkpointData['title'])

		local checkpointFrame = CheckpointScrollFrame:FindFirstChild( frameName )
		if checkpointFrame then
			continue
		end

		checkpointFrame = UIFolder.TemplateOption:Clone()
		checkpointFrame.Name = frameName
		checkpointFrame.LayoutOrder = index

		local splits = string.split(checkpointData['model_name'], '_')
		if splits[1] == 'models' then
			table.remove(splits, 1)
		end
		if string.match(splits[#splits], 'v%d+$') then
			table.remove(splits, #splits)
		end
		checkpointFrame.Label.Text = table.concat(splits, ' ')

		checkpointFrame.Button.Activated:Connect(function()
			selectedInformation.checkpoint = checkpointData['title']
			OnSelectedInfoChanged()
		end)

		checkpointFrame.Parent = CheckpointScrollFrame
	end

	-- deselect current checkpoint if it no longer exists
	if selectedInformation.checkpoint and not table.find( activeCheckpointTitles, selectedInformation.checkpoint ) then
		warn('Checkpoint ' .. tostring(selectedInformation.checkpoint) .. ' is now unavailable, a new one has been automatically been selected.')
		selectedInformation.checkpoint = activeCheckpointTitles[1]
		hasSelectedInfoChanged = true
	end

	for _, checkpointFrame in ipairs( CheckpointScrollFrame:GetChildren() ) do
		if checkpointFrame:IsA("Frame") and not table.find( activeCheckpointNames, checkpointFrame.Name ) then
			checkpointFrame:Destroy()
		end
	end

	-- TODO: vaes
	local VAEsScrollFrame = DiffusionUI.Options.Frame.Menus.Models.Scroll.VAEScroll
	local activeVAENames = { }

	for index, vaeData in ipairs( CurrentStableDiffusionInfo.vaes ) do
		table.insert( activeVAENames, vaeData.name )

		local vaeFrame = VAEsScrollFrame:FindFirstChild( vaeData.name )
		if vaeFrame then
			continue
		end

		vaeFrame = UIFolder.TemplateOption:Clone()
		vaeFrame.Name = vaeData.name
		vaeFrame.LayoutOrder = index
		vaeFrame.Label.Text = vaeData.name

		vaeFrame.Button.Activated:Connect(function()
			if selectedInformation.vae == vaeData.name then
				selectedInformation.vae = nil
			else
				selectedInformation.vae = vaeData.name
			end
			OnSelectedInfoChanged()
		end)

		vaeFrame.Parent = VAEsScrollFrame
	end

	for _, vaeFrame in ipairs( VAEsScrollFrame:GetChildren() ) do
		if vaeFrame:IsA("Frame") and not table.find( activeVAENames, vaeFrame.Name ) then
			vaeFrame:Destroy()
		end
	end

	if selectedInformation.vae and not table.find( activeVAENames, selectedInformation.vae ) then
		warn('VAE ' .. tostring(selectedInformation.checkpoint) .. ' is now unavailable and has been set to blank.')
		selectedInformation.vae = activeVAENames[1]
		hasSelectedInfoChanged = true
	end

	for _, vaeFrame in ipairs( VAEsScrollFrame:GetChildren() ) do
		if vaeFrame:IsA("Frame") and not table.find( activeVAENames, vaeFrame.Name ) then
			vaeFrame:Destroy()
		end
	end

	-- LORAs
	local LORAsScrollFrame = DiffusionUI.Options.Frame.Menus.LORAs.Scroll

	local sharedIndexCounter = 1
	local categoryOrder = { 'samplers', 'hypernetworks', 'loras' }

	for _, categoryName in ipairs( categoryOrder ) do
		if not CurrentStableDiffusionInfo[categoryName] then
			warn('No information was found in stable diffusion info for category: ' .. tostring(categoryName))
			continue
		end

		-- divider
		local categoryDivider = LORAsScrollFrame:FindFirstChild( categoryName..'Divider' )
		if not categoryDivider then
			categoryDivider = UIFolder.TemplateDivider:Clone()
			categoryDivider.Name = categoryName..'Divider'
			categoryDivider.Label.Text = string.upper(categoryName)
			categoryDivider.Parent = LORAsScrollFrame
		end
		categoryDivider.LayoutOrder = sharedIndexCounter
		sharedIndexCounter += 1

		-- scroll
		local categoryScroll = LORAsScrollFrame:FindFirstChild( categoryName..'Scroll' )
		if not categoryScroll then
			categoryScroll = UIFolder.TemplateScroll:Clone()
			categoryScroll.Name = categoryName..'Scroll'
			categoryScroll.Parent = LORAsScrollFrame
		end
		categoryScroll.LayoutOrder = sharedIndexCounter
		sharedIndexCounter += 1

		for _, frame in ipairs( categoryScroll:GetChildren()  ) do
			if frame:IsA("Frame") then
				frame:Destroy()
			end
		end

		-- each item in the scroll
		for modelIndex, modelInfo in ipairs( CurrentStableDiffusionInfo[categoryName] ) do
			local frameName = ( typeof(modelInfo) == "string" and modelInfo or modelInfo['path'] )
			local selectedIndex = typeof(modelInfo) == 'string' and modelInfo or modelInfo['name']

			local modelFrame  = UIFolder.TemplateOption:Clone()
			modelFrame.Name = frameName
			modelFrame:SetAttribute('index', selectedIndex)

			modelFrame.Button.Activated:Connect(function()
				if typeof(modelInfo) == 'table' then
					-- allow adding/removing of this item
					if not selectedInformation[categoryName] then
						selectedInformation[categoryName] = { }
					end
					local index = table.find( selectedInformation[categoryName], selectedIndex )
					if index then
						table.remove(selectedInformation[categoryName], index)
					else
						table.insert( selectedInformation[categoryName], selectedIndex )
					end
				else
					-- set it to this value
					selectedInformation[categoryName] = modelInfo
				end
				OnSelectedInfoChanged()
			end)

			local isSelected = typeof(selectedInformation[categoryName]) == 'table' and (typeof( modelInfo ) ~= "string" and table.find( selectedInformation[categoryName], selectedIndex ) or (selectedInformation[categoryName] == selectedIndex))
			modelFrame.Label.TextColor3 = isSelected and selectedColor3 or notSelectedColor3

			if typeof( modelInfo ) == 'string' then
				modelFrame.Label.Text = modelInfo
			else
				modelFrame.Label.Text = modelInfo['alias'] .. ' (' .. (modelInfo['type'] or 'unknown') .. ')'
			end
			modelFrame.LayoutOrder = modelIndex
			modelFrame.Parent = categoryScroll
		end

	end

	-- divider
	local categoryDivider = LORAsScrollFrame:FindFirstChild( 'EmbeddingDivider' )
	if not categoryDivider then
		categoryDivider = UIFolder.TemplateDivider:Clone()
		categoryDivider.Name = 'EmbeddingDivider'
		categoryDivider.Label.Text = string.upper('Embeddings')
		categoryDivider.Parent = LORAsScrollFrame
	end
	categoryDivider.LayoutOrder = sharedIndexCounter
	sharedIndexCounter += 1

	-- scroll
	local categoryScroll = LORAsScrollFrame:FindFirstChild( 'EmbeddingsScroll' )
	if not categoryScroll then
		categoryScroll = UIFolder.TemplateScroll:Clone()
		categoryScroll.Name = 'EmbeddingsScroll'
		categoryScroll.Parent = LORAsScrollFrame
	end
	categoryScroll.LayoutOrder = sharedIndexCounter
	sharedIndexCounter += 1

	for _, frame in ipairs( categoryScroll:GetChildren() ) do
		if frame:IsA("Frame") then
			frame:Destroy()
		end
	end

	local counter = 0
	for embeddingName, embeddingData in pairs(CurrentStableDiffusionInfo.embeddings) do
		local actualName = embeddingData['sd_checkpoint_name'] or embeddingName

		local modelFrame = UIFolder.TemplateOption:Clone()
		modelFrame.Name = embeddingName
		modelFrame:SetAttribute('index', actualName)

		modelFrame.Button.Activated:Connect(function()
			-- allow adding/removing of this item
			if not selectedInformation.embeddings then
				selectedInformation.embeddings = { }
			end
			local index = table.find( selectedInformation.embeddings, actualName )
			if index then
				-- print('remove: ', index)
				table.remove( selectedInformation.embeddings, index )
			else
				-- print('insert: ', actualName)
				table.insert( selectedInformation.embeddings, actualName )
			end
			OnSelectedInfoChanged()
		end)

		local isSelected = selectedInformation.embeddings and table.find(selectedInformation.embeddings, actualName)
		modelFrame.Label.TextColor3 = isSelected and selectedColor3 or notSelectedColor3
		modelFrame.Label.Text = actualName
		modelFrame.LayoutOrder = counter

		counter += 1

		modelFrame.Parent = categoryScroll
	end

	if hasSelectedInfoChanged then
		OnSelectedInfoChanged()
	end
end

-- menu buttons
local MenuFrames = { }

local function ToggleMenuFrames( TargetFrame )
	for _, Frame in ipairs( MenuFrames ) do
		Frame.Visible = (Frame==TargetFrame)
	end
end

for _, Frame in ipairs( DiffusionUI.Options.Frame.MenuButtons:GetChildren() ) do
	if not Frame:IsA("Frame") then
		continue
	end

	local TargetFrame = DiffusionUI.Options.Frame.Menus:FindFirstChild( Frame.Name )
	if not TargetFrame then
		warn('Could not find the target menu frame for button of name: ' .. tostring(Frame.Name) )
		continue
	end

	Frame.Button.Activated:Connect(function()
		ToggleMenuFrames( TargetFrame )
	end)
	table.insert( MenuFrames, TargetFrame )
end

DiffusionUI.Options.Submit.Activated:Connect(function()
	if not selectedInformation.checkpoint then
		-- print('no selected checkpoint')
		return
	end

	if DiffusionUI.Options.Frame.PromptOptions.Scroll.Prompt.Input.Text == '' then
		-- print('no prompt')
		return
	end

	-- print(HttpService:JSONEncode(data))

	local additionalString = {''}
	for _, item in ipairs( selectedInformation.loras or {} ) do
		table.insert( additionalString, string.format('<lora:%s:0.2>', item) )
	end
	for _, item in ipairs( selectedInformation.hypernetworks or {} ) do
		table.insert( additionalString, string.format('<hypernetwork:%s:0.2>', item) )
	end
	local additionalNeg = {''}
	for _, item in ipairs( selectedInformation.embeddings or {} ) do
		table.insert( additionalNeg, item )
	end

	--[[local imageData = ]]
	StableDiffusionShared.Text2ImageSugar({
		selectedInformation.checkpoint,
		selectedInformation.vae,
		DiffusionUI.Options.Frame.PromptOptions.Scroll.Prompt.Input.Text ..  table.concat(additionalString, ' '),
		DiffusionUI.Options.Frame.PromptOptions.Scroll.NegativePrompt.Input.Text .. table.concat(additionalNeg, ' '),
		30,
		8,
		selectedInformation.samplers,
		512,
		512,
		1,
		1,
		nil
	})

	-- client render
	--[[
		print('decoding pixels')
		local pixelBoard = StableDiffusionShared.DecodePixels( imageData[2] )

		print('rendering image start')
		local startTime = os.clock()
		local textBoard = StableDiffusionShared.PixelBoardModule.ConvertPixelsToTextForm( pixelBoard )

		StableDiffusionShared.PixelBoardModule.DisplayTextForm( textBoard, PixelBoardFrame )
		print( 'The operation took '.. tostring(os.clock() - startTime).. ' seconds to render on image labels.' )
	]]

end)

OnSelectedInfoChanged()
if not LocalPlayer.Character then
	LocalPlayer.CharacterAdded:Wait()
end

-- update info loop
task.spawn(function()
	while true do
		local stime = time()
		local stableDiffusionInfo = InvokeStableDiffusion(StableDiffusionShared.CommandEnums.GetStableDiffusionInfo)
		print('It took ', math.round((time() - stime) * 100) / 100, ' to query the stable diffusion info.')
		if not stableDiffusionInfo then
			warn('Could not pull stable diffusion info from server.')
			return
		end
		CurrentStableDiffusionInfo = stableDiffusionInfo

		UpdateStableDiffusionUIInfo()

		task.wait(10)
	end
end)

print('Press P to toggle the stable diffusion prompt UI.')
