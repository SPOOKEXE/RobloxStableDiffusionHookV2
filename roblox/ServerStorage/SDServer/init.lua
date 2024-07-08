
local SDServer = require(script.SDServer)
type InstanceInfo = SDServer.InstanceInfo
type OperationMetaData = SDServer.OperationMetaData
type OperationProgress = SDServer.OperationProgress
type Txt2ImgParameters = SDServer.Txt2ImgParameters

local ReplicatedStorage = game:GetService("ReplicatedStorage")
local SDShared = require(ReplicatedStorage:WaitForChild('SDShared'))

local SystemsContainer = {}

local Module = {}

function Module.Start()

end

function Module.Init(otherSystems)
	SystemsContainer = otherSystems
end

return Module
