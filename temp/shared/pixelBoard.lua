
-- // Module // --
local Module = {}

function Module.ConvertPixelsToTextForm( pixels )
	-- generate all independants
	local pixelBoard = { }
	for _, rowPixel in ipairs( pixels ) do

		-- fill in colors
		local rowPixels = { }
		local currentCharacterCount = 0
		for _, value in ipairs( rowPixel ) do
			if typeof(value) == "string" then
				-- compressed value unpack
				local count, rgb = unpack(string.split(value, 'y'))
				count = tonumber(count)
				currentCharacterCount += count
				local r,g,b = unpack(string.split(rgb,','))
				table.insert(rowPixels, string.format(BasePixelText, tonumber(r) * 5, tonumber(g) * 5, tonumber(b) * 5, string.rep(Character, count)))
			else
				-- individual pixel
				local text = string.format(BasePixelText, value[1] * 5, value[2] * 5, value[3] * 5, Character)
				table.insert(rowPixels, text)
				currentCharacterCount += 1
			end
		end

		-- fill in blanks with black (center image by putting 1 pixel on the left and right)
		if currentCharacterCount < 256 then
			local blackPixel = string.format(BasePixelText, 0,0,0, Character)
			local remainingAmount = (256 - currentCharacterCount)
			for _ = 1, math.floor(remainingAmount / 2) do
				table.insert(rowPixels, blackPixel)
				table.insert(rowPixels, 1, blackPixel)
			end
			-- if its an odd number, padd on the far right
			if remainingAmount % 2 == 1 then
				table.insert(rowPixels, blackPixel)
			end
		end

		-- insert to table after joining pixels together
		table.insert(pixelBoard, table.concat(rowPixels, ''))
	end

	-- TODO: if #pixels < 256, fill in top with half and bottom with half to pad it to center

	return pixelBoard

end

return Module
