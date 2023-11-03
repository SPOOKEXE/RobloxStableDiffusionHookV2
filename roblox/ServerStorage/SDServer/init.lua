
--[[
	ENDPOINTS = {
		"get_hash_status" : data = { hash = "" }
		"get_hash_progress" : data = { hash = "" }
		"get_hash_queue" : data = { hash = "" }
		"get_hash_image" : data = { hash = "" }
		"post_txt2img" : data = { } -- prompt
	}
]]

local HttpService = game:GetService('HttpService')

local ReplicatedStorage = game:GetService('ReplicatedStorage')
local StableDiffusionShared = require(ReplicatedStorage:WaitForChild('SDShared'))

local PYTHON_SERVER_URL : string = 'https://b81fe2245419.ngrok.app'

local function RequestAsync( url : string, body : any)
	local response = nil
	local success, err = pcall(function()
		-- print("Requesting to ", Url, " with body ", Body)
		response = HttpService:RequestAsync({
			Url = url,
			Method = "POST",
			Headers = {
				["Content-Type"] = "application/json",
			},
			Body = HttpService:JSONEncode(body),
		})
	end)

	if not success then
		warn(err)
		return nil
	end

	local isJSON = (response.Headers['content-type'] == 'application/json')
	return isJSON and HttpService:JSONDecode(response.Body)['message']
end

--[[
local function typeAssert( param_name, value, ... )
	local isOfType = false
	for _, expected_type in ipairs( { ... } ) do
		if not isOfType then
			isOfType = typeof(value) == expected_type
		end
	end

	if not isOfType then
		error( string.format("%s must be of types: %s.", param_name, table.concat({...}, ' or ') ) )
	end
end
]]

-- // Module // --
local Module = {}

function Module.GetSDInstances() : { table }
	return RequestAsync(PYTHON_SERVER_URL, { command = 'get_sd_instances', })
end

function Module.GetHashStatus() : number

end

function Module.GetHashProgress()

end

function Module.GetHashQueue()

end

function Module.GetHashImage()

end

function Module.Text2Image()

end

return Module
