
local ServerStorage = game:GetService('ServerStorage')
local StableDiffusionServer = require(ServerStorage:WaitForChild('SDServer'))

local ReplicatedStorage = game:GetService('ReplicatedStorage')
local StableDiffusionShared = require(ReplicatedStorage:WaitForChild('SDShared'))

local data = StableDiffusionServer.GetSDInstances()
print(data)
