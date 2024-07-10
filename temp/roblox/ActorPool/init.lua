
--[[
	Actor Pool Module:
	------------------

	# Actor Setup
	Change the contents of the ActorModule.lua inside the Actor folder and add commands via functions.

	# Actor Pool Usage
	local ActorPoolModule = require(ActorPoolPath)

	# Results
	local ResultsOrdered = ActorPoolModule.DistributeCalculation(
		'V3Mag',
		{
			{ Vector3.one, Vector3.zero },
			{ Vector3.one, Vector3.zero },
			{ Vector3.one, Vector3.zero },
			{ Vector3.one, Vector3.zero },
			{ Vector3.one, Vector3.zero },
			{ Vector3.one, Vector3.zero },
			{ Vector3.one, Vector3.zero },
			{ Vector3.one, Vector3.zero },
		},
		true
	)

	print( ResultsOrdered )

]]

local RunService = game:GetService('RunService')
local HttpService = game:GetService('HttpService')

local OutboundBind = Instance.new('BindableEvent')
OutboundBind.Name = 'Outbound'
OutboundBind.Parent = script

local InboundBind = Instance.new('BindableEvent')
InboundBind.Name = 'Inbound'
InboundBind.Parent = script

local ActorFolder = Instance.new('Folder')
ActorFolder.Name = 'ActorContainer'
ActorFolder.Parent = RunService:IsServer() and game:GetService('ServerScriptService') or game:GetService('Players').LocalPlayer:WaitForChild('PlayerScripts')

-- // Module // --
local Module = {}

Module.ActorPool = {}
Module.UUIDPool = {}
Module.TargetActorAmont = 0

Module.JobQueue = {}

function Module.CreateActor() : Actor
	local UUID = HttpService:GenerateGUID(false)

	local Actor = Instance.new('Actor')
	Actor.Name = 'ActorPool_Instance'
	Actor:SetAttribute('UUID', UUID)

	local OutboundReference = Instance.new('ObjectValue')
	OutboundReference.Name = 'OutboundReference'
	OutboundReference.Value = OutboundBind
	OutboundReference.Parent = Actor

	local InboundReference = Instance.new('ObjectValue')
	InboundReference.Name = 'InboundReference'
	InboundReference.Value = InboundBind
	InboundReference.Parent = Actor

	for _, Object in ipairs( script:GetChildren() ) do
		Object:Clone().Parent = Actor
	end

	if RunService:IsServer() then
		Actor.ActorServer.Disabled = false
	else
		Actor.ActorClient.Disabled = false
	end
	Actor.Parent = ActorFolder

	return UUID, Actor
end

function Module.CleanupExtraActors()
	while #Module.ActorPool > Module.TargetActorAmont do
		local Actor = table.remove( Module.ActorPool, 1 )
		Module.DestroyActor( Actor )
	end
end

function Module.DestroyActor( actorInstance : Actor )
	actorInstance:Destroy()
end

function Module.SetTargetActorAmount( amount : number )
	Module.TargetActorAmont = amount
	if #Module.ActorPool < amount then
		Module.AppendActors( amount - #Module.ActorPool )
	elseif #Module.ActorPool > amount then
		Module.CleanupExtraActors()
	end
end

function Module.AppendActors( amount : number )
	if amount == 0 then
		return
	end

	for _ = 1, amount do
		local UUID, Actor = Module.CreateActor()
		table.insert(Module.UUIDPool, UUID)
		table.insert(Module.ActorPool, Actor)
	end
end

function Module.PopJobId( jobId : string )
	local index = table.find( Module.JobQueue, jobId )
	if index then
		table.remove(Module.JobQueue, index)
	end
end

function Module.WaitForJobAvailability( ) : (boolean, string)
	local JobId = HttpService:GenerateGUID(false)
	table.insert(Module.JobQueue, JobId)
	local index = table.find(Module.JobQueue, JobId)
	while index and index ~= 1 do
		task.wait(0.05)
		index = table.find(Module.JobQueue, JobId)
	end
	return index == 1, JobId
end

--[[
	Distribute ONE command with A LIST OF parameters across pooled actors.
]]
function Module.DistributeCalculation(
	command : string,
	parameters_list : table,
	allow_more_actors : boolean,
	do_cleanup : boolean
) : { any? }

	assert( typeof(command) == 'string' or typeof(command) == 'number', 'Command must be a string or number.' )
	assert( typeof(parameters_list) == 'table', 'Parameters must be a table.' )
	assert( typeof(allow_more_actors) == 'boolean', 'allow_more_actors must be a boolean.' )
	assert( typeof(do_cleanup) == 'boolean', 'do_cleanup must be a boolean.' )

	print('Awaiting Job')
	local IsJobValid, JobId = Module.WaitForJobAvailability( )
	if not IsJobValid then
		return nil
	end

	print('Job Available!')
	if allow_more_actors then
		Module.AppendActors( math.max(0, #parameters_list - #Module.UUIDPool) )
	end

	print('Actors Available: ', #Module.UUIDPool)

	local Results = table.create( #parameters_list, false )
	local AvailableUUIDs = table.clone( Module.UUIDPool )

	local connection; connection = InboundBind.Event:Connect(function(UUID : string, resultIndex : number, success : boolean, results : any?)
		if success then
			Results[ resultIndex ] = #results == 1 and results[1] or results
		else
			warn('Failed to run command on actor: ' .. tostring( results[1] ) )
		end
		table.insert(AvailableUUIDs, UUID)
	end)

	print('Distributing Calculation.')

	local RemainingParameters = table.clone(parameters_list)
	local ParamCounter = 1
	while #RemainingParameters > 0 do
		print('Waiting for ', #RemainingParameters, ' parameters to be calculated.')
		while #RemainingParameters > 0 and #AvailableUUIDs > 0 do
			-- print("Remaining to calculate: ", #RemainingParameters)
			local UUID = table.remove(AvailableUUIDs, 1)
			local Params = table.remove(RemainingParameters, 1)
			OutboundBind:Fire( UUID, ParamCounter, command, Params )
			ParamCounter += 1
		end
		task.wait()
	end

	connection:Disconnect()

	print('Calculations completed, returning ', #Results, ' values.')
	Module.PopJobId(JobId)
	if do_cleanup then
		Module.CleanupExtraActors()
	end

	return Results
end

Module.SetTargetActorAmount( 1 )

return Module
