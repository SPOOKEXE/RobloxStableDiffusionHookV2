
local zlib = require(script.zlib)

local Module = {}

Module.zlib = zlib.Zlib :: {Compress : (string, { level : number }?) -> string, Decompress : (string) -> string}
Module.Event = require(script.Event)
Module.Maid = require(script.Maid)
Module.RemoteService = require(script.RemoteService)

Module.OperationStatusEnums = {
	IN_QUEUE = 0,
	IN_PROGRESS = 1,
	COMPLETED = 2,
	CANCELED = 3,
	ERRORED = 4,
}

Module.RemoteRateLimits = {
	Default = 1,

	-- GetSDInstances = 5,
	-- Text2Image = 5,

	-- ClearPrivateImage = 3,
	-- VoteClearPublicImage = 3,

	-- GetHashStatus = 0.5,
	-- GetHashQueue = 0.5,
	-- GetHashProgress = 0.5,
	-- GetHashImage = 5,
}

Module.RemoteEnums = {

	-- prompting

	-- operations

}

function Module.OperationStatusFromValue( target : number ) : string?
	for name, value in Module.OperationStatusEnums do
		if value == target then
			return name
		end
	end
	return nil
end

Module.AspectRatioMap = {
	["512x512"] = {512, 512},
	["512x768"] = {512, 768},
	["512x1024"] = {512, 1024},
	["768x512"] = {768, 512},
	["768x768"] = {768, 768},
	["768x1024"] = {768, 1024},
	["1024x512"] = {1024, 512},
	["1024x768"] = {1024, 768},
	["1024x1024"] = {1024, 1024},
}

function Module.ToHex( value : string ) : (string, number)
	return value:gsub('.', function(c)
		return string.format('%02X', string.byte(c))
	end)
end

function Module.FromHex( value : string ) : (string, number)
	return value:gsub('..', function(cc)
		return string.char(tonumber(cc, 16))
	end)
end

return Module