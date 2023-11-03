local gf = require(script.Parent:WaitForChild('gf'))
local util = require(script.Parent:WaitForChild('util'))

-- local bit = require(script.Parent:WaitForChild("bit"))
local bit = bit32

local Methods = {}

Methods.SBox = {}
Methods.iSBox = {}

Methods.table0 = {}
Methods.table1 = {}
Methods.table2 = {}
Methods.table3 = {}

Methods.tableInv0 = {}
Methods.tableInv1 = {}
Methods.tableInv2 = {}
Methods.tableInv3 = {}

Methods.rCon = {
	0x01000000,
	0x02000000,
	0x04000000,
	0x08000000,
	0x10000000,
	0x20000000,
	0x40000000,
	0x80000000,
	0x1b000000,
	0x36000000,
	0x6c000000,
	0xd8000000,
	0xab000000,
	0x4d000000,
	0x9a000000,
	0x2f000000
}

function Methods.affinMap(byte)
	local mask = 0xf8
	local result = 0
	for _ = 1,8 do
		result = bit.lshift(result,1)
		local parity = util.byteParity(bit.band(byte,mask))
		result = result + parity
		local lastbit = bit.band(mask, 1)
		mask = bit.band(bit.rshift(mask, 1),0xff)
		if lastbit ~= 0 then
			mask = bit.bor(mask, 0x80)
		else
			mask = bit.band(mask, 0x7f)
		end
	end
	return bit.bxor(result, 0x63)
end

function Methods.calcSBox()
	for i = 0, 255 do
		local inverse = (i ~= 0) and gf.invert(i) or i
		local mapped = Methods.affinMap(inverse)
		Methods.SBox[i] = mapped
		Methods.iSBox[mapped] = i
	end
end

function Methods.calcRoundTables()
	for x = 0,255 do
		local byte = Methods.SBox[x]
		Methods.table0[x] = util.putByte(gf.mul(0x03, byte), 0)
						  + util.putByte(             byte , 1)
						  + util.putByte(             byte , 2)
						  + util.putByte(gf.mul(0x02, byte), 3)
		Methods.table1[x] = util.putByte(             byte , 0)
						  + util.putByte(             byte , 1)
						  + util.putByte(gf.mul(0x02, byte), 2)
						  + util.putByte(gf.mul(0x03, byte), 3)
		Methods.table2[x] = util.putByte(             byte , 0)
						  + util.putByte(gf.mul(0x02, byte), 1)
						  + util.putByte(gf.mul(0x03, byte), 2)
						  + util.putByte(             byte , 3)
		Methods.table3[x] = util.putByte(gf.mul(0x02, byte), 0)
						  + util.putByte(gf.mul(0x03, byte), 1)
						  + util.putByte(             byte , 2)
						  + util.putByte(             byte , 3)
	end
end

function Methods.calcInvRoundTables()
	for x = 0,255 do
		local byte = Methods.iSBox[x]
		Methods.tableInv0[x] = util.putByte(gf.mul(0x0b, byte), 0)
							 + util.putByte(gf.mul(0x0d, byte), 1)
							 + util.putByte(gf.mul(0x09, byte), 2)
							 + util.putByte(gf.mul(0x0e, byte), 3)
		Methods.tableInv1[x] = util.putByte(gf.mul(0x0d, byte), 0)
							 + util.putByte(gf.mul(0x09, byte), 1)
							 + util.putByte(gf.mul(0x0e, byte), 2)
							 + util.putByte(gf.mul(0x0b, byte), 3)
		Methods.tableInv2[x] = util.putByte(gf.mul(0x09, byte), 0)
							 + util.putByte(gf.mul(0x0e, byte), 1)
							 + util.putByte(gf.mul(0x0b, byte), 2)
							 + util.putByte(gf.mul(0x0d, byte), 3)
		Methods.tableInv3[x] = util.putByte(gf.mul(0x0e, byte), 0)
							 + util.putByte(gf.mul(0x0b, byte), 1)
							 + util.putByte(gf.mul(0x0d, byte), 2)
							 + util.putByte(gf.mul(0x09, byte), 3)
	end
end

function Methods.rotWord(word)
	local tmp = bit.band(word,0xff000000)
	return (bit.lshift(word,8) + bit.rshift(tmp,24)) 
end

function Methods.subWord(word)
	return util.putByte(Methods.SBox[util.getByte(word,0)],0)
		 + util.putByte(Methods.SBox[util.getByte(word,1)],1)
		 + util.putByte(Methods.SBox[util.getByte(word,2)],2)
		 + util.putByte(Methods.SBox[util.getByte(word,3)],3)
end

function Methods.invMixColumnOld(word)
	local b0 = util.getByte(word,3)
	local b1 = util.getByte(word,2)
	local b2 = util.getByte(word,1)
	local b3 = util.getByte(word,0)

	return util.putByte(gf.add(gf.add(gf.add(gf.mul(0x0b, b1),
											 gf.mul(0x0d, b2)),
											 gf.mul(0x09, b3)),
											 gf.mul(0x0e, b0)),3)
		 + util.putByte(gf.add(gf.add(gf.add(gf.mul(0x0b, b2),
											 gf.mul(0x0d, b3)),
											 gf.mul(0x09, b0)),
											 gf.mul(0x0e, b1)),2)
		 + util.putByte(gf.add(gf.add(gf.add(gf.mul(0x0b, b3),
											 gf.mul(0x0d, b0)),
											 gf.mul(0x09, b1)),
											 gf.mul(0x0e, b2)),1)
		 + util.putByte(gf.add(gf.add(gf.add(gf.mul(0x0b, b0),
											 gf.mul(0x0d, b1)),
											 gf.mul(0x09, b2)),
											 gf.mul(0x0e, b3)),0)
end

function Methods.invMixColumn(word)
	local b0 = util.getByte(word,3)
	local b1 = util.getByte(word,2)
	local b2 = util.getByte(word,1)
	local b3 = util.getByte(word,0)

	local t = bit.bxor(b3,b2)
	local u = bit.bxor(b1,b0)
	local v = bit.bxor(t,u)
	v = bit.bxor(v,gf.mul(0x08,v))
	local w = bit.bxor(v,gf.mul(0x04, bit.bxor(b2,b0)))
	v = bit.bxor(v,gf.mul(0x04, bit.bxor(b3,b1)))

	return util.putByte( bit.bxor(bit.bxor(b3,v), gf.mul(0x02, bit.bxor(b0,b3))), 0)
		 + util.putByte( bit.bxor(bit.bxor(b2,w), gf.mul(0x02, t              )), 1)
		 + util.putByte( bit.bxor(bit.bxor(b1,v), gf.mul(0x02, bit.bxor(b0,b3))), 2)
		 + util.putByte( bit.bxor(bit.bxor(b0,w), gf.mul(0x02, u              )), 3)
end

function Methods.addRoundKey(state, key, round)
	for i = 0, 3 do
		state[i] = bit.bxor(state[i], key[round*4+i])
	end
end

function Methods.doRound(origState, dstState)
	dstState[0] =  bit.bxor(bit.bxor(bit.bxor(
				Methods.table0[util.getByte(origState[0],3)],
				Methods.table1[util.getByte(origState[1],2)]),
				Methods.table2[util.getByte(origState[2],1)]),
				Methods.table3[util.getByte(origState[3],0)])

	dstState[1] =  bit.bxor(bit.bxor(bit.bxor(
				Methods.table0[util.getByte(origState[1],3)],
				Methods.table1[util.getByte(origState[2],2)]),
				Methods.table2[util.getByte(origState[3],1)]),
				Methods.table3[util.getByte(origState[0],0)])

	dstState[2] =  bit.bxor(bit.bxor(bit.bxor(
				Methods.table0[util.getByte(origState[2],3)],
				Methods.table1[util.getByte(origState[3],2)]),
				Methods.table2[util.getByte(origState[0],1)]),
				Methods.table3[util.getByte(origState[1],0)])

	dstState[3] =  bit.bxor(bit.bxor(bit.bxor(
				Methods.table0[util.getByte(origState[3],3)],
				Methods.table1[util.getByte(origState[0],2)]),
				Methods.table2[util.getByte(origState[1],1)]),
				Methods.table3[util.getByte(origState[2],0)])
end

function Methods.doLastRound(origState, dstState)
	dstState[0] = util.putByte(Methods.SBox[util.getByte(origState[0],3)], 3)
				+ util.putByte(Methods.SBox[util.getByte(origState[1],2)], 2)
				+ util.putByte(Methods.SBox[util.getByte(origState[2],1)], 1)
				+ util.putByte(Methods.SBox[util.getByte(origState[3],0)], 0)

	dstState[1] = util.putByte(Methods.SBox[util.getByte(origState[1],3)], 3)
				+ util.putByte(Methods.SBox[util.getByte(origState[2],2)], 2)
				+ util.putByte(Methods.SBox[util.getByte(origState[3],1)], 1)
				+ util.putByte(Methods.SBox[util.getByte(origState[0],0)], 0)

	dstState[2] = util.putByte(Methods.SBox[util.getByte(origState[2],3)], 3)
				+ util.putByte(Methods.SBox[util.getByte(origState[3],2)], 2)
				+ util.putByte(Methods.SBox[util.getByte(origState[0],1)], 1)
				+ util.putByte(Methods.SBox[util.getByte(origState[1],0)], 0)

	dstState[3] = util.putByte(Methods.SBox[util.getByte(origState[3],3)], 3)
				+ util.putByte(Methods.SBox[util.getByte(origState[0],2)], 2)
				+ util.putByte(Methods.SBox[util.getByte(origState[1],1)], 1)
				+ util.putByte(Methods.SBox[util.getByte(origState[2],0)], 0)
end

function Methods.doInvRound(origState, dstState)
	dstState[0] =  bit.bxor(bit.bxor(bit.bxor(
				Methods.tableInv0[util.getByte(origState[0],3)],
				Methods.tableInv1[util.getByte(origState[3],2)]),
				Methods.tableInv2[util.getByte(origState[2],1)]),
				Methods.tableInv3[util.getByte(origState[1],0)])

	dstState[1] =  bit.bxor(bit.bxor(bit.bxor(
				Methods.tableInv0[util.getByte(origState[1],3)],
				Methods.tableInv1[util.getByte(origState[0],2)]),
				Methods.tableInv2[util.getByte(origState[3],1)]),
				Methods.tableInv3[util.getByte(origState[2],0)])

	dstState[2] =  bit.bxor(bit.bxor(bit.bxor(
				Methods.tableInv0[util.getByte(origState[2],3)],
				Methods.tableInv1[util.getByte(origState[1],2)]),
				Methods.tableInv2[util.getByte(origState[0],1)]),
				Methods.tableInv3[util.getByte(origState[3],0)])

	dstState[3] =  bit.bxor(bit.bxor(bit.bxor(
				Methods.tableInv0[util.getByte(origState[3],3)],
				Methods.tableInv1[util.getByte(origState[2],2)]),
				Methods.tableInv2[util.getByte(origState[1],1)]),
				Methods.tableInv3[util.getByte(origState[0],0)])
end

function Methods.doInvLastRound(origState, dstState)
	dstState[0] = util.putByte(Methods.iSBox[util.getByte(origState[0],3)], 3)
				+ util.putByte(Methods.iSBox[util.getByte(origState[3],2)], 2)
				+ util.putByte(Methods.iSBox[util.getByte(origState[2],1)], 1)
				+ util.putByte(Methods.iSBox[util.getByte(origState[1],0)], 0)

	dstState[1] = util.putByte(Methods.iSBox[util.getByte(origState[1],3)], 3)
				+ util.putByte(Methods.iSBox[util.getByte(origState[0],2)], 2)
				+ util.putByte(Methods.iSBox[util.getByte(origState[3],1)], 1)
				+ util.putByte(Methods.iSBox[util.getByte(origState[2],0)], 0)

	dstState[2] = util.putByte(Methods.iSBox[util.getByte(origState[2],3)], 3)
				+ util.putByte(Methods.iSBox[util.getByte(origState[1],2)], 2)
				+ util.putByte(Methods.iSBox[util.getByte(origState[0],1)], 1)
				+ util.putByte(Methods.iSBox[util.getByte(origState[3],0)], 0)

	dstState[3] = util.putByte(Methods.iSBox[util.getByte(origState[3],3)], 3)
				+ util.putByte(Methods.iSBox[util.getByte(origState[2],2)], 2)
				+ util.putByte(Methods.iSBox[util.getByte(origState[1],1)], 1)
				+ util.putByte(Methods.iSBox[util.getByte(origState[0],0)], 0)
end

Methods.calcSBox()
Methods.calcRoundTables()
Methods.calcInvRoundTables()

-- // Module // --
local Module = {}
Module.ROUNDS = "rounds"
Module.KEY_TYPE = "type"
Module.ENCRYPTION_KEY=1
Module.DECRYPTION_KEY=2

function Module.expandEncryptionKey(key)
	local keySchedule = {}
	local keyWords = math.floor(#key / 4)
	if (keyWords ~= 4 and keyWords ~= 6 and keyWords ~= 8) or (keyWords * 4 ~= #key) then
		print("Invalid key size: ", keyWords)
		return nil
	end

	keySchedule[Module.ROUNDS] = keyWords + 6
	keySchedule[Module.KEY_TYPE] = Module.ENCRYPTION_KEY

	for i = 0,keyWords - 1 do
		keySchedule[i] = util.putByte(key[i*4+1], 3)
					   + util.putByte(key[i*4+2], 2)
					   + util.putByte(key[i*4+3], 1)
					   + util.putByte(key[i*4+4], 0)
	end
	for i = keyWords, (keySchedule[Module.ROUNDS] + 1)*4 - 1 do
		local tmp = keySchedule[i-1]
		if i % keyWords == 0 then
			tmp = Methods.rotWord(tmp)
			tmp = Methods.subWord(tmp)
			local index = math.floor(i/keyWords)
			tmp = bit.bxor(tmp,Methods.rCon[index])
		elseif keyWords > 6 and i % keyWords == 4 then
			tmp = Methods.subWord(tmp)
		end
		keySchedule[i] = bit.bxor(keySchedule[(i-keyWords)],tmp)
	end

	return keySchedule
end

function Module.expandDecryptionKey(key)
	local keySchedule = Module.expandEncryptionKey(key)
	if keySchedule == nil then
		return nil
	end

	keySchedule[Module.KEY_TYPE] = Module.DECRYPTION_KEY

	for i = 4, (keySchedule[Module.ROUNDS] + 1)*4 - 5 do
		keySchedule[i] = Methods.invMixColumnOld(keySchedule[i])
	end

	return keySchedule
end

function Module.encrypt(key, input, inputOffset, output, outputOffset)
	inputOffset = inputOffset or 1
	output = output or {}
	outputOffset = outputOffset or 1

	local state = {}
	local tmpState = {}
	if key[Module.KEY_TYPE] ~= Module.ENCRYPTION_KEY then
		print("No encryption key: ", key[Module.KEY_TYPE])
		return
	end

	state = util.bytesToInts(input, inputOffset, 4)
	Methods.addRoundKey(state, key, 0)

	local round = 1
	while round < key[Module.ROUNDS] - 1 do
		Methods.doRound(state, tmpState)
		Methods.addRoundKey(tmpState, key, round)
		round = round + 1

		Methods.doRound(tmpState, state)
		Methods.addRoundKey(state, key, round)
		round = round + 1
	end

	Methods.doRound(state, tmpState)
	Methods.addRoundKey(tmpState, key, round)
	round = round +1

	Methods.doLastRound(tmpState, state)
	Methods.addRoundKey(state, key, round)

	return util.intsToBytes(state, output, outputOffset)
end

function Module.decrypt(key, input, inputOffset, output, outputOffset)
	inputOffset = inputOffset or 1
	output = output or {}
	outputOffset = outputOffset or 1

	local state = {}
	local tmpState = {}

	if key[Module.KEY_TYPE] ~= Module.DECRYPTION_KEY then
		print("No decryption key: ", key[Module.KEY_TYPE])
		return
	end

	state = util.bytesToInts(input, inputOffset, 4)
	Methods.addRoundKey(state, key, key[Module.ROUNDS])

	local round = key[Module.ROUNDS] - 1
	while round > 2 do
		Methods.doInvRound(state, tmpState)
		Methods.addRoundKey(tmpState, key, round)
		round = round - 1

		Methods.doInvRound(tmpState, state)
		Methods.addRoundKey(state, key, round)
		round = round - 1
	end

	Methods.doInvRound(state, tmpState)
	Methods.addRoundKey(tmpState, key, round)
	round = round - 1

	Methods.doInvLastRound(tmpState, state)
	Methods.addRoundKey(state, key, round)

	return util.intsToBytes(state, output, outputOffset)
end

return Module