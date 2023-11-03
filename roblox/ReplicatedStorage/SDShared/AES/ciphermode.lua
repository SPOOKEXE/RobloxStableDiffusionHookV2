local aes = require(script.Parent:WaitForChild('aes'))
local util = require(script.Parent:WaitForChild('util'))
local buffer = require(script.Parent:WaitForChild('buffer'))

-- // Module // --
local Module = {}

--Syntatic sugar, it really needs this, considering how many characters it's going to process, lol.
function Module.encryptString(key, data, modeFunction)
	local iv = {0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0}
	local keySched = aes.expandEncryptionKey(key)
	local encryptedData = buffer.new()
	for i = 1, #data/16 do
		local offset = (i-1)*16 + 1
		local byteData = {string.byte(data,offset,offset +15)}
		modeFunction(keySched, byteData, iv)
		buffer.addString(encryptedData, string.char(unpack(byteData)))
	end
	return buffer.toString(encryptedData)
end

-- Electronic code book mode encrypt function
function Module.encryptECB(keySched, byteData, iv)
	aes.encrypt(keySched, byteData, 1, byteData, 1)
end

-- Cipher block chaining mode encrypt function
function Module.encryptCBC(keySched, byteData, iv)
	util.xorIV(byteData, iv)
	aes.encrypt(keySched, byteData, 1, byteData, 1)
	for j = 1,16 do
		iv[j] = byteData[j]
	end
end

-- Output feedback mode encrypt function
function Module.encryptOFB(keySched, byteData, iv)
	aes.encrypt(keySched, iv, 1, iv, 1)
	util.xorIV(byteData, iv)
end

-- Cipher feedback mode encrypt function
function Module.encryptCFB(keySched, byteData, iv)
	aes.encrypt(keySched, iv, 1, iv, 1)
	util.xorIV(byteData, iv)
	for j = 1,16 do
		iv[j] = byteData[j]
	end
end

function Module.decryptString(key, data, modeFunction)
	local iv = {0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0}
	local keySched
	if modeFunction == Module.decryptOFB or modeFunction == Module.decryptCFB then
		keySched = aes.expandEncryptionKey(key)
	else
		keySched = aes.expandDecryptionKey(key)
	end
	local decryptedData = buffer.new()
	for i = 1, #data/16 do
		local offset = (i-1)*16 + 1
		local byteData = {string.byte(data,offset,offset +15)}
		iv = modeFunction(keySched, byteData, iv)
		buffer.addString(decryptedData, string.char(unpack(byteData)))
	end
	return buffer.toString(decryptedData)
end

-- Electronic code book mode decrypt function
function Module.decryptECB(keySched, byteData, iv)
	aes.decrypt(keySched, byteData, 1, byteData, 1)
	return iv
end

-- Cipher block chaining mode decrypt function
function Module.decryptCBC(keySched, byteData, iv)
	local nextIV = {}
	for j = 1,16 do
		nextIV[j] = byteData[j]
	end
	aes.decrypt(keySched, byteData, 1, byteData, 1)
	util.xorIV(byteData, iv)
	return nextIV
end

-- Output feedback mode decrypt function
function Module.decryptOFB(keySched, byteData, iv)
	aes.encrypt(keySched, iv, 1, iv, 1)
	util.xorIV(byteData, iv)
	return iv
end

-- Cipher feedback mode decrypt function
function Module.decryptCFB(keySched, byteData, iv)
	local nextIV = {}
	for j = 1,16 do
		nextIV[j] = byteData[j]
	end
	aes.encrypt(keySched, iv, 1, iv, 1)
	util.xorIV(byteData, iv)
	return nextIV
end

return Module