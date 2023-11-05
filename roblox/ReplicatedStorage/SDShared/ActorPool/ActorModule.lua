
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

	DecodePixelsAndPixelify = function( pallete : table, row : table, baseRichText : string, pixelCharacter : string, width : number ) : table
		local totalCharacters = 0
		local rowPixels = {}
		for _, Value in ipairs( row ) do
			local count, value = 1, Value
			if typeof(Value) == 'string' then
				count, value = unpack(string.split(Value, 'y'))
				if tonumber(value) then
					-- pallete index, map to the value
					value = pallete[tonumber(value)]
				else
					-- unpack the rgb
					local r, g, b = string.split(value, ',')
					value = { tonumber(r), tonumber(g), tonumber(b) }
				end
			end
			count = tonumber(count)
			totalCharacters += count
			table.insert(rowPixels, string.format(baseRichText, value[1] * 5, value[2] * 5, value[3] * 5, string.rep(pixelCharacter, count)))
		end

		if totalCharacters < 256 then
			local blackPixel = string.format(baseRichText, 0,0,0, pixelCharacter)
			local remainingAmount = (256 - totalCharacters)
			for _ = 1, math.floor(remainingAmount / 2) do
				table.insert(rowPixels, blackPixel)
				table.insert(rowPixels, 1, blackPixel)
			end
			-- if its an odd number, padd on the far right
			if remainingAmount % 2 == 1 then
				table.insert(rowPixels, blackPixel)
			end
		end

		return table.concat(rowPixels, '')
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
