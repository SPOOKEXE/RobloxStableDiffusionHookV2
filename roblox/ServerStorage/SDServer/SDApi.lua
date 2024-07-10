
export type InstanceInfo = { sys_info : { [string] : any }, sd_info : { [string] : any }, }

export type OperationMetaData = { state : number, timestamp : number, error : string? }
export type OperationProgress = { eta : number }

export type Txt2ImgParameters = {
	roblox_user : { user_id : number, player_name : string, }?,
	timestamp : number?,
	checkpoint : string,
	prompt : string,
	negative : string?,
	steps : number?,
	cfg_scale : number?,
	sampler_name : string?,
	size : string?,
	seed : number?,
}

local HttpService = game:GetService('HttpService')

local ReplicatedStorage = game:GetService('ReplicatedStorage')
local SDShared = require(ReplicatedStorage:WaitForChild('SDShared'))

local ServerURL : string = 'http://127.0.0.1:500'

-- local RSA_KEY_SIZE : number = 1024

-- local RSAIdentifier : string? = nil -- so public key can be grabbed
-- local ServerPublicKey : {}? = nil -- to send server information
-- local ClientPrivateKey : {}? = nil -- to decode server responses

-- local function SetProperties(parent : any, properties : {[string] : any}?) : any
-- 	if typeof(properties) == 'table' then
-- 		for propName, propValue in properties do
-- 			parent[propName] = propValue
-- 		end
-- 	end
-- 	return parent
-- end

local function PrepareBody(body : any?) : string?
	return body and HttpService:JSONEncode(body)
end

local function PrepareHeaders() : {}
	return { ["Content-Type"] = "application/json", }
end

local function RequestAsync( method : 'POST' | 'GET', url : string, body : any?) : (boolean, { [string] : any })
	local success, data = pcall(function()
		return HttpService:RequestAsync({Url = url, Method = method, Headers = PrepareHeaders(), Body = PrepareBody(body),})
	end)

	if not success or not data.Success then
		warn(data)
		return false, data
	end

	local decodedBody = HttpService:JSONDecode(data.Body)

	if typeof(decodedBody) == "table" then
		if decodedBody['data'] then
			local hexDecoded : string, _ = SDShared.FromHex( decodedBody['data'] )
			decodedBody['data'] = SDShared.zlib.Decompress(hexDecoded)
		end
	end

	return true, decodedBody
end

local function typeAssertion( param_name : string, value : any?, ... : string? )
	local isOfType = false
	for _, expected_type in { ... } do
		if not isOfType then
			isOfType = (typeof(value) == expected_type)
		end
	end

	if not isOfType then
		error( string.format("%s must be of types: %s.", param_name, table.concat({...}, ' or ') ) )
	end
end

local function InternalGET( path : string ) : boolean
	return RequestAsync('GET', ServerURL .. path, nil)
end

local function InternalPOST( path : string, body : any? ) : (boolean, string)
	return RequestAsync('POST', ServerURL .. path, body)
end

-- local function EncodeRSA()

-- end

-- local function DecodeRSA()

-- end

local Module = {}

function Module.SetServerURL( url : string )
	ServerURL = url
end

-- '/'
function Module.Health() : boolean
	local success, _ = InternalGET('/')
	return (success == true)
end

-- '/setup_rsa'
-- function Module.SetupRSA() : boolean
-- 	if ServerPublicKey then
-- 		return true
-- 	end

-- 	-- generate identifier
-- 	if not RSAIdentifier then
-- 		RSAIdentifier = HttpService:GenerateGUID(false)
-- 	end

-- 	local public, private = GenerateKeyPair(RSA_KEY_SIZE)
-- 	ClientPrivateKey = private

-- 	local success, response = InternalPOST('/setup_rsa', {
-- 		identifier = RSAIdentifier,
-- 		public_key = public,
-- 	})

-- 	if not success then
-- 		ClientPrivateKey = nil
-- 		RSAIdentifier = nil
-- 		return false
-- 	end
-- end

-- '/get_public_key'
-- function Module.GetPublicKey() : (string, string)
-- 	if not RSAIdentifier then
-- 		return nil
-- 	end
-- 	local success, response = InternalPOST('/get_public_key', {identifier = RSAIdentifier})
-- 	if not success then
-- 		return nil
-- 	end
-- 	local splits = string.split(response, ',')
-- 	if #splits == 2 then
-- 		return nil
-- 	end
-- 	return table.unpack(splits)
-- end

-- '/total_instances'
function Module.GetInstancesCount() : number?
	local success, response = InternalGET('/total_instances')
	if not success then
		return nil
	end
	return tonumber( response )
end

-- '/queue_length'
function Module.GetQueueLength() : number?
	local success, response = InternalGET('/queue_length')
	if not success then
		return nil
	end
	return tonumber( response )
end

-- '/total_operations'
function Module.GetTotalActiveOperations() : number?
	local success, response = InternalGET('/total_operations')
	if not success then
		return nil
	end
	return tonumber( response )
end

-- '/get_instance_infos'
function Module.GetInstancesInfos() : { InstanceInfo }?
	local success, response = InternalGET('/get_instance_infos')
	if not success then
		return nil
	end
	return response
end

-- '/get_operation_status'
function Module.GetOperationStatus( operation_id : string ) : number?
	typeAssertion('operation_id', operation_id, 'string')
	local success, response = InternalPOST('/get_operation_status', {operation_id = operation_id})
	if not success then
		return nil
	end
	return response and tonumber(response)
end

-- '/is_operation_completed'
function Module.IsOperationCompleted( operation_id : string ) : boolean
	typeAssertion('operation_id', operation_id, 'string')
	local success, response = InternalPOST('/is_operation_completed', {operation_id = operation_id})
	if not success then
		return nil
	end
	return response
end

-- '/get_operation_metadata'
function Module.GetOperationMetaData( operation_id : string ) : OperationMetaData?
	typeAssertion('operation_id', operation_id, 'string')
	local success, response = InternalPOST('/is_operation_completed', {operation_id = operation_id})
	if not success then
		return nil
	end
	return response
end

-- '/get_operation_progress'
function Module.GetOperationProgress( operation_id : string ) : OperationProgress?
	typeAssertion('operation_id', operation_id, 'string')
	local success, response = InternalPOST('/get_operation_progress', {operation_id = operation_id})
	if not success then
		return nil
	end
	return response
end

-- '/cancel_operation'
function Module.CancelOperation( operation_id : string ) : nil
	typeAssertion('operation_id', operation_id, 'string')
	local _, _ = InternalPOST('/cancel_operation', {operation_id = operation_id})
end

-- '/get_operation_images'
function Module.GetOperationImages( operation_id : string ) : { {size : {number}, data : string | number} }
	typeAssertion('operation_id', operation_id, 'string')
	local success, response = InternalPOST('/get_operation_images', {operation_id = operation_id})
	if not success then
		return nil
	end
	return response
end

-- '/queue_txt2img'
function Module.QueueTxt2Img( params : Txt2ImgParameters ) : string?
	typeAssertion('roblox_user', params.roblox_user, 'table', 'nil')
	typeAssertion('timestamp', params.timestamp, 'number', 'nil')
	typeAssertion('checkpoint', params.checkpoint, 'string')
	typeAssertion('prompt', params.prompt, 'string')
	typeAssertion('negative', params.negative, 'string', 'nil')
	typeAssertion('steps', params.steps, 'number')
	typeAssertion('cfg_scale', params.cfg_scale, 'number', 'nil')
	typeAssertion('sampler_name', params.sampler_name, 'string')
	typeAssertion('size', params.size, 'string')
	typeAssertion('seed', params.seed, 'number')
	local success, response = InternalPOST('/queue_txt2img', params)
	if not success then
		warn(response)
		return nil
	end
	return response -- response is the operation id
end

return Module
