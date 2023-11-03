--local bit = require(script.Parent:WaitForChild("bit"))
local bit = bit32

local public = {}
local private = {}

function public.byteParity(byte)
	byte = bit.bxor(byte, bit.rshift(byte, 4))
	byte = bit.bxor(byte, bit.rshift(byte, 2))
	byte = bit.bxor(byte, bit.rshift(byte, 1))
	return bit.band(byte, 1)
end

function public.getByte(number, index)
	if index == 0 then
		return bit.band(number,0xff)
	end
	return bit.band(bit.rshift(number, index*8),0xff)
end

function public.putByte(number, index)
	if index == 0 then
		return bit.band(number,0xff)
	end
	return bit.lshift(bit.band(number,0xff),index*8)
end

function public.bytesToInts(bytes, start, n)
	local ints = {}
	for i = 0, n - 1 do
		ints[i] = public.putByte(bytes[start + (i*4)    ], 3)
				+ public.putByte(bytes[start + (i*4) + 1], 2)
				+ public.putByte(bytes[start + (i*4) + 2], 1)
				+ public.putByte(bytes[start + (i*4) + 3], 0)
	end
	return ints
end

function public.intsToBytes(ints, output, outputOffset, n)
	n = n or #ints
	for i = 0, n do
		for j = 0,3 do
			output[outputOffset + i*4 + (3 - j)] = public.getByte(ints[i], j)
		end
	end
	return output
end

function private.bytesToHex(bytes)
	local hexBytes = ""
	for _, byte in ipairs(bytes) do
		hexBytes = hexBytes .. string.format("%02x ", byte)
	end
	return hexBytes
end

function public.toHexString(data)
	local type = type(data)
	if type == "number" then
		return string.format("%08x",data)
	elseif type == "table" then
		return private.bytesToHex(data)
	elseif type == "string" then
		return private.bytesToHex({string.byte(data, 1, #data)})
	end
	return data
end

function public.padByteString(data)
	local dataLength = #data

	local random1 = math.random(0,255)
	local random2 = math.random(0,255)

	local prefix = string.char(
		random1,
		random2,
		random1,
		random2,
		public.getByte(dataLength, 3),
		public.getByte(dataLength, 2),
		public.getByte(dataLength, 1),
		public.getByte(dataLength, 0)
	)

	data = prefix .. data
	local paddingLength = math.ceil(#data/16)*16 - #data
	local padding = ""
	for _ = 1, paddingLength do
		padding = padding .. string.char(math.random(0,255))
	end
	return data .. padding
end

function private.properlyDecrypted(data)
	local random = {string.byte(data,1,4)}
	return (random[1] == random[3]) and (random[2] == random[4])
end

function public.unpadByteString(data)
	if not private.properlyDecrypted(data) then
		return nil
	end
	local dataLength = public.putByte(string.byte(data,5), 3)
					+ public.putByte(string.byte(data,6), 2)
					+ public.putByte(string.byte(data,7), 1)
					+ public.putByte(string.byte(data,8), 0)

	return string.sub(data,9,8+dataLength)
end

function public.xorIV(data, iv)
	for i = 1,16 do
		data[i] = bit.bxor(data[i], iv[i])
	end
end

return public