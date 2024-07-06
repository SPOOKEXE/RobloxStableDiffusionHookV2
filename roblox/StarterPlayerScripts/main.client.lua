
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local SDShared = require(ReplicatedStorage:WaitForChild('SDShared'))

local SDClient = require(script.Parent.SDClient)

local Players = game:GetService("Players")
local LocalPlayer = Players.LocalPlayer

local ScreenGui = LocalPlayer:WaitForChild('PlayerGui'):WaitForChild('SDUI')
local Container = ScreenGui.Container
local Progress = ScreenGui.Progress
local Visibility = ScreenGui.Visibility

local IsContainerOpen = false
local ContainerOpenPosition = UDim2.fromScale(0.008, 0.5)
local ContainerClosePosition = UDim2.fromScale(-0.5, 0.5)
local ProgressOpenPosition = UDim2.fromScale(0.251, 0.327)
local ProgressClosePosition = UDim2.fromScale(-0.5, 0.327)

local function TweenPosition(Frame : Frame, endPosition : UDim2, duration : number?)
	Frame:TweenPosition(endPosition, Enum.EasingDirection.InOut, Enum.EasingStyle.Sine, duration or 0.5, true)
end

Container.Position = IsContainerOpen and ContainerOpenPosition or ContainerClosePosition
Progress.Position = IsContainerOpen and ProgressOpenPosition or ProgressClosePosition
Visibility.Label.Text = IsContainerOpen and '<' or '>'
Visibility.Button.Activated:Connect(function()
	IsContainerOpen = not IsContainerOpen
	TweenPosition( Container, IsContainerOpen and ContainerOpenPosition or ContainerClosePosition, nil )
	TweenPosition( Progress, IsContainerOpen and ProgressOpenPosition or ProgressClosePosition, nil )
	Visibility.Label.Text = IsContainerOpen and '<' or '>'
end)

local CategoryToFrame = {}

local function ToggleCategory(ButtonFrame)
	for Button, Page in CategoryToFrame do
		local isOpen = (ButtonFrame == Button)
		Button.Button.TextColor3 = isOpen and Color3.fromRGB(200, 200, 0) or Color3.new(1, 1, 1)
		Page.Visible = isOpen
	end
end

for _, Frame in Container.Categories.Scroll:GetChildren() do
	if Frame:IsA("Frame") then
		local TargetPage = Container.Pages:FindFirstChild(Frame.Name)
		if not TargetPage then
			warn('Could not find target page to match category button: ' .. Frame.Name)
			continue
		end
		CategoryToFrame[Frame] = TargetPage
		Frame.Button.Activated:Connect(function()
			ToggleCategory(Frame)
		end)
	end
end

ToggleCategory(Container.Categories.Scroll.Info)
