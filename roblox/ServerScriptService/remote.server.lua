
local Players = game:GetService('Players')

local ServerStorage = game:GetService('ServerStorage')
local SDServer = require(ServerStorage:WaitForChild('SDServer'))

local ReplicatedStorage = game:GetService("ReplicatedStorage")
-- local SDShared = require(ReplicatedStorage:WaitForChild('SDShared'))
local RemoteEnums = require(ReplicatedStorage:WaitForChild('RemoteEnums'))

local SDRemoteFunction = Instance.new('RemoteFunction')
SDRemoteFunction.Name = 'SDFunction'
SDRemoteFunction.Parent = ReplicatedStorage

local CooldownCache = {} -- comamnd cooldowns

-- print( SDServer.GetSDInstances() )

local function HandleOnServerInvoke(LocalPlayer, value)
	-- decode info
	local Args = RemoteEnums.DecompressJSON(value)
	local EnumValue = table.remove(Args, 1)

	-- check if its a valid command.
	local commandName = RemoteEnums.GetCommandNameFromValue( EnumValue )
	if not commandName then
		local message = string.format('Invalid Command - Cannot find with value %s', tostring(EnumValue))
		return RemoteEnums.CompressJSON({false, message})
	end

	--[[-- command queue check
	local UserOperations = {}
	if commandName == 'Text2Image' and UserOperations[ LocalPlayer ] then
		local message = 'Cannot queue another prompt until your current one has finished.'
		return RemoteEnums.CompressJSON({false, message})
	end]]

	-- command cooldown.
	if not CooldownCache[ LocalPlayer ] then
		CooldownCache[ LocalPlayer ] =  { }
	end

	local CooldownDuration = RemoteEnums.GetCommandCooldown( commandName )
	local debounceTime = CooldownCache[ LocalPlayer ][ commandName ]
	if debounceTime and time() < debounceTime then
		local message = string.format('You are currently on cooldown for another %s seconds.', tostring( math.round(debounceTime - time())) )
		return RemoteEnums.CompressJSON({false, message})
	end
	CooldownCache[ LocalPlayer ][ commandName ] = time() + CooldownDuration -- prevent spam for command

	-- find the api function
	local targetFunction = SDServer[ commandName ]
	if not targetFunction then
		local message = string.format('There is no such API function named %s', tostring(commandName))
		return RemoteEnums.CompressJSON({false, message})
	end

	-- request via api
	if commandName == 'Text2Image' then
		-- log info (to ban those bad actors)
		table.insert(Args, 1, LocalPlayer.Name)
		table.insert(Args, 2, LocalPlayer.UserId)
	end

	-- call the api method and return the results
	local results = { pcall(targetFunction, unpack(Args)) }
	table.remove(results, 1) -- pop the 'network' success boolean (not needed)
	return RemoteEnums.CompressJSON(results)
end

Players.PlayerRemoving:Connect(function(LocalPlayer)
	CooldownCache[LocalPlayer] = nil
end)
SDRemoteFunction.OnServerInvoke = HandleOnServerInvoke
