--local bit = require(script.Parent:WaitForChild("bit"))
local bit = bit32

local Enums = {}
Enums.n = 0x100
Enums.ord = 0xff
Enums.irrPolynom = 0x11b
Enums.exp = {}
Enums.log = {}

-- // Module // --
local Module = {}
Module.Enums = Enums

function Module.add(operand1, operand2)
	return bit.bxor(operand1,operand2)
end

function Module.sub(operand1, operand2)
	return bit.bxor(operand1,operand2)
end

function Module.invert(operand)
	if operand == 1 then
		return 1
	end
	local exponent = Enums.ord - Enums.log[operand]
	return Enums.exp[exponent]
end

function Module.mul(operand1, operand2)
	if operand1 == 0 or operand2 == 0 then
		return 0
	end
	local exponent = Enums.log[operand1] + Enums.log[operand2]
	if exponent >= Enums.ord then
		exponent = exponent - Enums.ord
	end
	return  Enums.exp[exponent]
end

function Module.div(operand1, operand2)
	if operand1 == 0  then
		return 0
	end
	local exponent = Enums.log[operand1] - Enums.log[operand2]
	if exponent < 0 then
		exponent = exponent + Enums.ord
	end
	return Enums.exp[exponent]
end

function Module.printLog()
	for i = 1, Enums.n do
		print("log(", i-1, ")=", Enums.log[i-1])
	end
end

function Module.printExp()
	for i = 1, Enums.n do
		print("exp(", i-1, ")=", Enums.exp[i-1])
	end
end

function Enums.initMulTable()
	local a = 1
	for i = 0,Enums.ord-1 do
		Enums.exp[i] = a
		Enums.log[a] = i
		a = bit.bxor(bit.lshift(a, 1), a)
		if a > Enums.ord then
			a = Module.sub(a, Enums.irrPolynom)
		end
	end
end

Enums.initMulTable()

return Module