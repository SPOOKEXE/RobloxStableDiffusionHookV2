local HttpService = game:GetService("HttpService")

local SDSharedModule = require(script.Parent.SDShared)

local Module = {}

Module.OperationStatus = {
	NonExistent = -1,
	InQueue = 0,
	InProgress = 1,
	Finished = 2,
	Errored = 3,
}

Module.Commands = {
	GetSDInstances = 1, -- get distributed instances infos
	Text2Image = 2, -- request prompt

	ClearPrivateImage = 3, -- roblox-stuff
	VoteClearPublicImage = 4, -- roblox-stuff

	GetHashStatus = 5, -- get the status number
	GetHashQueue = 6, -- get the queue position
	GetHashProgress = 7, -- get the hash progress (if generating)
	GetHashImage = 8, -- get the image from the hash
}

Module.Cooldowns = {
	Default = 1,

	GetSDInstances = 5,
	Text2Image = 5,

	ClearPrivateImage = 3,
	VoteClearPublicImage = 3,

	GetHashStatus = 0.5,
	GetHashQueue = 0.5,
	GetHashProgress = 0.5,
	GetHashImage = 5,
}

function Module.GetCommandNameFromValue( number : number ) : string?
	for commandName, commandValue in pairs( Module.Commands ) do
		if commandValue == number then
			return commandName
		end
	end
	return nil
end

function Module.GetCommandCooldown( commandName : string ) : number
	return Module.Cooldowns[commandName] or Module.Cooldowns.Default
end

function Module.CompressJSON( value : table ) : string
	return SDSharedModule.zlib.Zlib.Compress( HttpService:JSONEncode( value ) )
end

function Module.DecompressJSON( value : string ) : table
	return HttpService:JSONDecode( SDSharedModule.zlib.Zlib.Decompress( value ) )
end

return Module
