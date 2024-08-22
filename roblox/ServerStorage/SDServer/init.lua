
local SDApi = require(script.SDApi)
type InstanceInfo = SDApi.InstanceInfo
type OperationMetaData = SDApi.OperationMetaData
type OperationProgress = SDApi.OperationProgress
type Txt2ImgParameters = SDApi.Txt2ImgParameters

local ReplicatedStorage = game:GetService("ReplicatedStorage")
local SDShared = require(ReplicatedStorage:WaitForChild('SDShared'))

local SDRemoteEvent : RemoteEvent = SDShared.RemoteService.GetRemote('SDEvent', 'RemoteEvent', false)

local SystemsContainer = {}

local Module = {}

function Module.ConvertLoraInput( name : string, weight : number? ) : string
	if weight then
		weight = math.clamp(weight, 0, 1)
	else
		weight = 1
	end
	return string.format('<lora:%s:%s>', name, weight)
end

function Module.GetSDInstanceInfo() : InstanceInfo?
	local instances = SDApi.GetInstancesInfos()
	return instances and instances[1]
end

function Module.QueueTxt2Img( params : Txt2ImgParameters ) : string?

end

function Module.GetOperationStatus( operation_id : string ) : number?

end

function Module.GetOperationProgress( operation_id : string ) : OperationProgress?

end

function Module.IsOperationCompleted( operation_id : string ) : boolean

end

function Module.GetOperationError() : string?

end

function Module.TestPrompt()

	SDApi.SetServerURL('http://127.0.0.1:5100')

	if not SDApi.Health() then
		warn('SDApi is not available - stopping.')
		return
	end

	local operation_id = SDApi.QueueTxt2Img({
		checkpoint = 'aamAnyloraAnimeMixAnime_v1.safetensors [354b8c571d]',
		prompt = '<lora:liz_smart:1> lizsmart, pink hair, color, bangs, earrings, smile, long hair, looking at viewer',
		cfg_scale = 7,
		negative = '',
		roblox_user = { user_id = 1, player_name = 'spook' },
		sampler_name = 'Euler a',
		size = '512x512',
		steps = 25,
		seed = -1,
	})

	print(operation_id)

	while true do
		task.wait(1)
		local status = SDApi.GetOperationStatus(operation_id)
		print(status)
		print(SDShared.OperationStatusFromValue(status))
		local completed = SDApi.IsOperationCompleted(operation_id)
		print(completed)
		if completed then
			break
		end
		print( SDApi.GetOperationProgress(operation_id) )
	end

	local status = SDApi.GetOperationStatus(operation_id)
	print(status)
	if status == SDShared.OperationStatusEnums.COMPLETED then
		local images = SDApi.GetOperationImages(operation_id)
		print(images)
	elseif status == SDShared.OperationStatusEnums.ERRORED then
		local metadata = SDApi.GetOperationMetaData(operation_id).error
		print('Operation has errored! ', metadata)
	elseif status == SDShared.OperationStatusEnums.CANCELED then
		print('Operation was canceled!')
	end

end

function Module.ParseRemoteData()

end

function Module.Start()

	task.spawn(Module.TestPrompt)

	SDRemoteEvent.OnServerEvent:Connect(function(LocalPlayer : Player, Job : number, ... : any?)
		if Job == SDShared.Re
	end)

end

function Module.Init()

end

return Module
