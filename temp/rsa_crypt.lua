local RSA = {}

-- Helper function: Compute the greatest common divisor
local function gcd(a, b)
	while b ~= 0 do
		a, b = b, a % b
	end
	return a
end

-- Helper function: Compute the modular multiplicative inverse
local function modInverse(e, phi)
	local t, newT = 0, 1
	local r, newR = phi, e
	while newR ~= 0 do
		local quotient = math.floor(r / newR)
		t, newT = newT, t - quotient * newT
		r, newR = newR, r - quotient * newR
	end
	if r > 1 then
		error("e is not invertible")
	end
	if t < 0 then
		t = t + phi
	end
	return t
end

-- Helper function: Compute the power modulo
local function modPow(base, exp, mod)
	local result = 1
	base = base % mod
	while exp > 0 do
		if exp % 2 == 1 then
			result = (result * base) % mod
		end
		exp = math.floor(exp / 2)
		base = (base * base) % mod
	end
	return result
end

-- Function: Generate RSA keys
function RSA.generateKeys(p, q)
	local n = p * q
	local phi = (p - 1) * (q - 1)
	local e = 3

	-- Ensure e and phi are coprime
	while gcd(e, phi) ~= 1 do
		e = e + 2
	end

	local d = modInverse(e, phi)

	return {publicKey = {e = e, n = n}, privateKey = {d = d, n = n}}
end

-- Function: Encrypt message chunks using RSA encryption
function RSA.encryptStringChunks(publicKey, message, chunkSize)
	local e, n = publicKey.e, publicKey.n
	local cipherText = {}
	for i = 1, #message, chunkSize do
		local chunk = message:sub(i, i + chunkSize - 1)
		local encryptedChunk = {}
		for j = 1, #chunk do
			local m = string.byte(chunk, j)
			table.insert(encryptedChunk, modPow(m, e, n))
		end
		table.insert(cipherText, encryptedChunk)
	end
	return cipherText
end

-- Function: Decrypt message chunks using RSA decryption
function RSA.decryptStringChunks(privateKey, cipherText)
	local d, n = privateKey.d, privateKey.n
	local message = {}
	for i = 1, #cipherText do
		local encryptedChunk = cipherText[i]
		local decryptedChunk = {}
		for j = 1, #encryptedChunk do
			local c = encryptedChunk[j]
			local m = modPow(c, d, n)
			table.insert(decryptedChunk, string.char(m))
		end
		table.insert(message, table.concat(decryptedChunk))
	end
	return table.concat(message)
end

-- Example usage
local p = 61  -- Choose two prime numbers
local q = 53
local chunkSize = 4  -- Example chunk size

local keys = RSA.generateKeys(p, q)
local publicKey = keys.publicKey
local privateKey = keys.privateKey

local message = "Hello, Roblox!"
local encryptedChunks = RSA.encryptStringChunks(publicKey, message, chunkSize)
local decryptedMessage = RSA.decryptStringChunks(privateKey, encryptedChunks)

print("Original Message:", message)
print("Encrypted Chunks:")
for i, chunk in ipairs(encryptedChunks) do
	print(i, table.concat(chunk, " "))
end
print("Decrypted Message:", decryptedMessage)
