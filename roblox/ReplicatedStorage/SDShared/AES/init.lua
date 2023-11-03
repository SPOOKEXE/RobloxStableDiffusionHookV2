
local ciphermode = require(script:WaitForChild('ciphermode'))
local util = require(script:WaitForChild('util'))

local Enums = {}
Enums.AES128 = 16
Enums.AES192 = 24
Enums.AES256 = 32

Enums.ECBMODE = 1
Enums.CBCMODE = 2
Enums.OFBMODE = 3
Enums.CFBMODE = 4

local function pwToKey(password, keyLength)
	local padLength = keyLength
	if keyLength == Enums.AES192 then
		padLength = 32
	end

	if padLength > #password then
		password = password .. string.rep( string.char(0), padLength - #password )
	else
		password = string.sub(password, 1, padLength)
	end

	local pwBytes = {string.byte(password, 1, #password)}
	password = ciphermode.encryptString(pwBytes, password, ciphermode.encryptCBC)
	password = string.sub(password, 1, keyLength)
	return { string.byte(password,1,#password) }
end

-- // Module // --
local Module = {}
Module.Enums = Enums

function Module.encrypt(password, data, keyLength, mode) : string?
	mode = mode or Enums.CBCMODE
	keyLength = keyLength or Enums.AES128

	local key = pwToKey(password, keyLength)
	local paddedData = util.padByteString(data)
	if mode == Enums.ECBMODE then
		return ciphermode.encryptString(key, paddedData, ciphermode.encryptECB)
	elseif mode == Enums.CBCMODE then
		return ciphermode.encryptString(key, paddedData, ciphermode.encryptCBC)
	elseif mode == Enums.OFBMODE then
		return ciphermode.encryptString(key, paddedData, ciphermode.encryptOFB)
	elseif mode == Enums.CFBMODE then
		return ciphermode.encryptString(key, paddedData, ciphermode.encryptCFB)
	end

	return nil
end

function Module.decrypt(password, data, keyLength, mode)
	mode = mode or Enums.CBCMODE
	keyLength = keyLength or Enums.AES128

	local key = pwToKey(password, keyLength)
	local plain
	if mode == Enums.ECBMODE then
		plain = ciphermode.decryptString(key, data, ciphermode.decryptECB)
	elseif mode == Enums.CBCMODE then
		plain = ciphermode.decryptString(key, data, ciphermode.decryptCBC)
	elseif mode == Enums.OFBMODE then
		plain = ciphermode.decryptString(key, data, ciphermode.decryptOFB)
	elseif mode == Enums.CFBMODE then
		plain = ciphermode.decryptString(key, data, ciphermode.decryptCFB)
	end
	return util.unpadByteString(plain)
end

return Module
