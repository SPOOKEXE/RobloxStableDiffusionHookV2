
local zlib = require(script.zlib)

local Module = {}

Module.zlib = zlib.Zlib :: {Compress : (string, { level : number }?) -> string, Decompress : (string) -> string}

Module.OperationStatusEnums = {
	IN_QUEUE = 0,
	IN_PROGRESS = 1,
	COMPLETED = 2,
	CANCELED = 3,
	ERRORED = 4,
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