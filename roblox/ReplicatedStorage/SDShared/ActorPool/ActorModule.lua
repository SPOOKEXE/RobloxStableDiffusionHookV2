
local ActorInstance = script.Parent
local ActorUUID = ActorInstance:GetAttribute('UUID')

local OutboundEvent = ActorInstance:WaitForChild('OutboundReference').Value :: BindableEvent
local InboundEvent = ActorInstance:WaitForChild('InboundReference').Value :: BindableEvent

assert( typeof(ActorUUID) == 'string', 'Actor was not given a UUID.' )
assert( typeof(OutboundEvent) == 'Instance' and OutboundEvent:IsA('BindableEvent'), 'Actor was not given a reference to the bindable event.' )
assert( typeof(InboundEvent) == 'Instance' and InboundEvent:IsA('BindableEvent'), 'Actor was not given a reference to the bindable event.' )

-- // Module // --
local Module = {}

Module.Commands = {

	DecodeRow = function( pallete : table, row : table ) : table
		--[[
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
			return table.concat(rowPixels, '')
		]]
	end,

	PixelifyRow = function( rowValues : { table | string }, baseRichText : string, pixel : string, width : number ) : ( { string }, number )
		--[[
			local Pixels = {}
			local totalCharacters = 0
			for _, Value in ipairs( rowValues ) do
				local count, value = 1, Value
				if typeof(Value) == 'string' then
					count, value = string.split(Value, 'y')
					count = tonumber(count)
					local r, g, b = string.split(value, ',')
					value = { tonumber(r), tonumber(g), tonumber(b) }
				end
				totalCharacters += count
				table.insert(Pixels, string.format(baseRichText, unpack(value), string.rep(pixel, count)))
			end

			if totalCharacters < 256 then
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

			return Pixels, totalCharacters
		]]
	end,

}

function Module.HandleCommand( command : string | number, ... : any? ) : any?
	assert( Module.Commands[command], 'No such command in actor commands! ' .. tostring(command) )
	return Module.Commands[command](...)
end

function Module.Init()

end

function Module.Start()

	-- ConnectParallel automatically starts desynchronized
	OutboundEvent.Event:ConnectParallel(function( UUID : string, ParamCounter : number, command : string, arguments : { any? } )
		if ActorUUID == UUID then
			local result = { pcall(Module.HandleCommand, command, unpack(arguments)) }
			local success = table.remove(result, 1)
			-- WRITE PARALLEL ENABLED
			InboundEvent:Fire( UUID, ParamCounter, success, result )
		end
	end)

end

return Module
