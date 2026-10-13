-- Tree of Life V0.5 - Africa Savanna Village runtime environment
-- This script deliberately replaces only generated visual layers. Existing
-- portals, quest scripts, gathering nodes, wildlife, spawns, and dungeon
-- triggers remain owned by the original game systems.

local Workspace = game:GetService("Workspace")
local ServerStorage = game:GetService("ServerStorage")

local continents = Workspace:WaitForChild("Continents")
local africa = continents:WaitForChild("Africa")
local assets = ServerStorage:WaitForChild("AfricaV05Assets", 20)

local openWorld = africa:WaitForChild("OpenWorld", 30)
if not openWorld then
	warn("AfricaV05: OpenWorld did not initialize")
	return
end

-- Let the original runtime art generators finish, then replace only their
-- disposable visual folders. Functional node Models stay under OpenWorld.
local started = os.clock()
repeat
	task.wait(0.25)
until africa:FindFirstChild("Art") or os.clock() - started > 12
task.wait(1)

local oldArt = africa:FindFirstChild("Art")
if oldArt then
	oldArt:Destroy()
end

local oldBiome = openWorld:FindFirstChild("Biome")
if oldBiome then
	oldBiome:Destroy()
end

local terrainFolder = openWorld:FindFirstChild("Terrain")
if terrainFolder then
	for _, child in ipairs(terrainFolder:GetChildren()) do
		if child.Name == "Hill" or child.Name == "Trunk" or child.Name == "Leaf" or child.Name == "Rock" then
			child:Destroy()
		end
	end
end

-- Hide only the legacy decorative trees placed directly beneath Africa.
-- The backup made by the installer retains their original state.
for _, child in ipairs(africa:GetChildren()) do
	if child:IsA("BasePart") and (child.Name == "Trunk" or child.Name == "Leaf") then
		child.Transparency = 1
		child.CanCollide = false
		child.CanQuery = false
	end
end

local art = Instance.new("Folder")
art.Name = "Art"
art:SetAttribute("Generator", "AfricaV05Runtime")
art:SetAttribute("Version", "0.5")
art.Parent = africa

-- The original prototype uses large world-space labels that overwhelm an
-- aerial view. Keep their information, but bring them into the same visual
-- scale as the rebuilt landmarks.
for _, descendant in ipairs(africa:GetDescendants()) do
	if descendant:IsA("BillboardGui") and not descendant:IsDescendantOf(art) then
		descendant.Size = UDim2.fromOffset(150, 42)
		descendant.MaxDistance = 110
	end
end

local centerPart = africa:FindFirstChild("Dirt") or africa:FindFirstChild("Plaza") or africa:FindFirstChild("HomeSpawn")
local center = centerPart and Vector3.new(centerPart.Position.X, 0, centerPart.Position.Z) or Vector3.new(-538.5, 0, 2359.3)
local groundY = 0.35
local rng = Random.new(5052026)

local COLORS = {
	sand = Color3.fromRGB(209, 168, 88),
	sandLight = Color3.fromRGB(232, 193, 111),
	sandDark = Color3.fromRGB(169, 118, 68),
	dryGrass = Color3.fromRGB(157, 151, 63),
	grass = Color3.fromRGB(100, 137, 47),
	leaves = Color3.fromRGB(58, 126, 48),
	leavesLight = Color3.fromRGB(135, 174, 57),
	bark = Color3.fromRGB(91, 51, 30),
	barkLight = Color3.fromRGB(132, 79, 39),
	rock = Color3.fromRGB(150, 104, 72),
	rockLight = Color3.fromRGB(184, 132, 82),
	stone = Color3.fromRGB(112, 91, 74),
	turquoise = Color3.fromRGB(37, 161, 164),
	coral = Color3.fromRGB(200, 75, 49),
	gold = Color3.fromRGB(235, 170, 55),
	cream = Color3.fromRGB(242, 207, 133),
	water = Color3.fromRGB(48, 151, 177),
}

local function part(parent, name, size, cframe, color, material, shape, collide)
	local p = Instance.new("Part")
	p.Name = name
	p.Anchored = true
	p.CanCollide = collide == true
	p.CanTouch = false
	p.CanQuery = true
	p.Size = size
	p.CFrame = cframe
	p.Color = color
	p.Material = material or Enum.Material.SmoothPlastic
	p.TopSurface = Enum.SurfaceType.Smooth
	p.BottomSurface = Enum.SurfaceType.Smooth
	if shape then
		p.Shape = shape
	end
	p.Parent = parent
	return p
end

local function disk(parent, name, position, diameterX, diameterZ, height, color, material, collide)
	return part(
		parent,
		name,
		Vector3.new(height, diameterX, diameterZ),
		CFrame.new(position) * CFrame.Angles(0, 0, math.rad(90)),
		color,
		material,
		Enum.PartType.Cylinder,
		collide
	)
end

local function ball(parent, name, position, size, color, material, collide)
	return part(parent, name, size, CFrame.new(position), color, material, Enum.PartType.Ball, collide)
end

local function beam(parent, name, a, b, width, color, material, collide)
	local delta = b - a
	return part(
		parent,
		name,
		Vector3.new(width, width, delta.Magnitude),
		CFrame.lookAt((a + b) / 2, b),
		color,
		material,
		nil,
		collide
	)
end

local function path(parent, name, a, b, width, bend)
	local segments = math.max(5, math.floor((b - a).Magnitude / 24))
	local last = a
	for i = 1, segments do
		local t = i / segments
		local p = a:Lerp(b, t)
		local wave = math.sin(t * math.pi) * (bend or 0)
		local side = Vector3.new(-(b - a).Z, 0, (b - a).X).Unit
		p += side * wave
		local mid = (last + p) / 2
		part(
			parent,
			name,
			Vector3.new(width, 0.28, (p - last).Magnitude + 1),
			CFrame.lookAt(Vector3.new(mid.X, groundY + 0.16, mid.Z), Vector3.new(p.X, groundY + 0.16, p.Z)),
			COLORS.sandLight,
			Enum.Material.Sandstone,
			nil,
			false
		)
		last = p
	end
end

local function label(parent, position, text, color)
	local post = part(parent, "LandmarkPost", Vector3.new(1.1, 8, 1.1), CFrame.new(position + Vector3.new(0, 4, 0)), COLORS.bark, Enum.Material.Wood, nil, true)
	local board = part(parent, "LandmarkBoard", Vector3.new(13, 4, 0.7), CFrame.new(position + Vector3.new(0, 8, 0)), COLORS.barkLight, Enum.Material.WoodPlanks, nil, false)
	local gui = Instance.new("BillboardGui")
	gui.Name = "Label"
	gui.Adornee = board
	gui.Size = UDim2.fromOffset(168, 46)
	gui.StudsOffset = Vector3.new(0, 0.3, 0)
	gui.MaxDistance = 115
	gui.AlwaysOnTop = false
	gui.Parent = board
	local textLabel = Instance.new("TextLabel")
	textLabel.Size = UDim2.fromScale(1, 1)
	textLabel.BackgroundTransparency = 1
	textLabel.Text = text
	textLabel.TextColor3 = color or COLORS.cream
	textLabel.TextStrokeTransparency = 0.15
	textLabel.TextScaled = true
	textLabel.Font = Enum.Font.FredokaOne
	textLabel.Parent = gui
	return post
end

local function grassClump(parent, position, scale, lush)
	local model = Instance.new("Model")
	model.Name = lush and "GreenGrassClump" or "DryGrassClump"
	model.Parent = parent
	local color = lush and COLORS.grass or COLORS.dryGrass
	for blade = 1, 5 do
		local angle = (blade / 5) * math.pi * 2 + rng:NextNumber(-0.22, 0.22)
		local height = rng:NextNumber(2.5, 5.5) * scale
		local offset = Vector3.new(math.cos(angle) * 0.8 * scale, height / 2, math.sin(angle) * 0.8 * scale)
		part(
			model,
			"Blade",
			Vector3.new(0.22 * scale, height, 0.36 * scale),
			CFrame.new(position + offset) * CFrame.Angles(rng:NextNumber(-0.14, 0.14), angle, rng:NextNumber(-0.22, 0.22)),
			color,
			Enum.Material.Grass,
			nil,
			false
		)
	end
	return model
end

local function termiteMound(parent, position, scale)
	local model = Instance.new("Model")
	model.Name = "TermiteMound"
	model.Parent = parent
	ball(model, "Mound", position + Vector3.new(0, 3.2 * scale, 0), Vector3.new(5.5, 8, 5.5) * scale, COLORS.sandDark, Enum.Material.Ground, true)
	ball(model, "MoundTop", position + Vector3.new(0.5 * scale, 7.2 * scale, 0), Vector3.new(3.4, 5.4, 3.4) * scale, COLORS.sandDark, Enum.Material.Ground, true)
	return model
end

local function rockCluster(parent, position, count, radius, scale)
	for i = 1, count do
		local angle = rng:NextNumber(0, math.pi * 2)
		local distance = rng:NextNumber(0, radius)
		local s = rng:NextNumber(scale * 0.55, scale * 1.25)
		ball(
			parent,
			"SavannaRock",
			position + Vector3.new(math.cos(angle) * distance, s * 0.28, math.sin(angle) * distance),
			Vector3.new(s * rng:NextNumber(0.8, 1.4), s * rng:NextNumber(0.55, 0.9), s),
			i % 2 == 0 and COLORS.rock or COLORS.rockLight,
			Enum.Material.Sandstone,
			true
		)
	end
end

local function lowAcacia(parent, position, scale)
	local model = Instance.new("Model")
	model.Name = "Acacia_Background"
	model.Parent = parent
	local h = 17 * scale
	local trunk = part(model, "Trunk", Vector3.new(2.2 * scale, h, 2.2 * scale), CFrame.new(position + Vector3.new(0, h / 2, 0)), COLORS.bark, Enum.Material.Wood, nil, true)
	model.PrimaryPart = trunk
	for i = 1, 4 do
		local angle = i * math.pi / 2 + rng:NextNumber(-0.35, 0.35)
		local tip = position + Vector3.new(math.cos(angle) * 6 * scale, h + rng:NextNumber(-1, 2), math.sin(angle) * 6 * scale)
		beam(model, "Branch", position + Vector3.new(0, h * 0.68, 0), tip, 1.2 * scale, COLORS.bark, Enum.Material.Wood, false)
		ball(model, "Canopy", tip + Vector3.new(0, 1.5 * scale, 0), Vector3.new(13, 3.8, 10) * scale, i % 2 == 0 and COLORS.leavesLight or COLORS.leaves, Enum.Material.Grass, false)
	end
	ball(model, "Canopy", position + Vector3.new(0, h + 2 * scale, 0), Vector3.new(15, 4.5, 12) * scale, COLORS.grass, Enum.Material.Grass, false)
	return model
end

local function baobab(parent, position, scale)
	local model = Instance.new("Model")
	model.Name = "Baobab"
	model.Parent = parent
	local h = 23 * scale
	local trunk = part(model, "Trunk", Vector3.new(7 * scale, h, 7 * scale), CFrame.new(position + Vector3.new(0, h / 2, 0)), COLORS.barkLight, Enum.Material.Wood, nil, true)
	model.PrimaryPart = trunk
	for i = 1, 6 do
		local angle = i * math.pi / 3
		local root = position + Vector3.new(0, h * 0.7, 0)
		local tip = position + Vector3.new(math.cos(angle) * 7 * scale, h + 5 * scale, math.sin(angle) * 7 * scale)
		beam(model, "Branch", root, tip, 1.7 * scale, COLORS.barkLight, Enum.Material.Wood, false)
		ball(model, "Leaves", tip, Vector3.new(6, 4, 6) * scale, COLORS.leavesLight, Enum.Material.Grass, false)
	end
	return model
end

local function herbPatch(parent, position, color)
	local model = Instance.new("Model")
	model.Name = "DecorativeHerbs"
	model:SetAttribute("ActivityType", "Herbs")
	model.Parent = parent
	for i = 1, 9 do
		local angle = rng:NextNumber(0, math.pi * 2)
		local r = rng:NextNumber(0.4, 3.8)
		local base = position + Vector3.new(math.cos(angle) * r, 0, math.sin(angle) * r)
		local stem = part(model, "Stem", Vector3.new(0.18, rng:NextNumber(1.2, 2.8), 0.18), CFrame.new(base + Vector3.new(0, 1, 0)), Color3.fromRGB(54, 137, 62), Enum.Material.Grass, nil, false)
		if i <= 5 then
			ball(model, "Flower", stem.Position + Vector3.new(0, stem.Size.Y / 2, 0), Vector3.new(0.8, 0.35, 0.8), color, Enum.Material.Neon, false)
		end
	end
	return model
end

local function marketStall(parent, position, yaw, canopyColor)
	local model = Instance.new("Model")
	model.Name = "MarketStall"
	model.Parent = parent
	local cf = CFrame.new(position) * CFrame.Angles(0, yaw, 0)
	for sx = -1, 1, 2 do
		for sz = -1, 1, 2 do
			part(model, "Post", Vector3.new(0.5, 7, 0.5), cf * CFrame.new(sx * 3.2, 3.5, sz * 2), COLORS.bark, Enum.Material.Wood, nil, true)
		end
	end
	part(model, "Counter", Vector3.new(7, 1, 4), cf * CFrame.new(0, 2.8, 0), COLORS.barkLight, Enum.Material.WoodPlanks, nil, true)
	part(model, "Canopy", Vector3.new(8.5, 0.45, 5.5), cf * CFrame.new(0, 7.2, 0), canopyColor, Enum.Material.Fabric, nil, false)
	for i = -2, 2 do
		ball(model, "Goods", (cf * CFrame.new(i * 1.1, 3.8, -0.5)).Position, Vector3.new(0.8, 0.8, 0.8), i % 2 == 0 and COLORS.gold or COLORS.turquoise, Enum.Material.SmoothPlastic, false)
	end
	return model
end

local function fallbackHut(parent, position, target, scale)
	local model = Instance.new("Model")
	model.Name = "VillageHut_Background"
	model.Parent = parent
	local cf = CFrame.lookAt(position, target)
	local wall = disk(model, "Wall", position + Vector3.new(0, 4.8 * scale, 0), 13 * scale, 13 * scale, 9.6 * scale, Color3.fromRGB(199, 124, 61), Enum.Material.Brick, true)
	wall.CFrame = cf * CFrame.new(0, 4.8 * scale, 0) * CFrame.Angles(0, 0, math.rad(90))
	ball(model, "ThatchRoof", position + Vector3.new(0, 10.2 * scale, 0), Vector3.new(19, 7, 19) * scale, Color3.fromRGB(152, 94, 38), Enum.Material.Grass, false)
	part(model, "Door", Vector3.new(3.4, 5.8, 0.5) * scale, cf * CFrame.new(0, 2.9 * scale, -6.5 * scale), COLORS.bark, Enum.Material.WoodPlanks, nil, false)
	return model
end

local function cloneHero(templateName, parent, name, position, target, scale)
	local template = assets and assets:FindFirstChild(templateName)
	if not template then
		return nil
	end
	local model = template:Clone()
	model.Name = name
	model.Parent = parent
	pcall(function()
		model:ScaleTo(scale)
	end)
	model:PivotTo(CFrame.lookAt(position, target))
	for _, descendant in ipairs(model:GetDescendants()) do
		if descendant:IsA("BasePart") then
			descendant.Anchored = true
			descendant.CanTouch = false
		end
	end
	return model
end

-- Full continent ground treatment. The functional OpenWorld ground remains
-- beneath this art layer as a safety net for gameplay scripts.
local land = Instance.new("Folder")
land.Name = "Land"
land.Parent = art
disk(land, "SavannaFoundation", center + Vector3.new(0, -5.5, 0), 830, 830, 12, COLORS.rock, Enum.Material.Sandstone, true)
disk(land, "SavannaTop", center + Vector3.new(0, -0.9, 0), 812, 812, 2.8, COLORS.sand, Enum.Material.Sand, true)
disk(land, "VillageSoil", center + Vector3.new(0, 0.15, 16), 190, 190, 0.3, COLORS.sandLight, Enum.Material.Ground, false)

for i = 1, 18 do
	local angle = i * math.pi * 2 / 18
	local radius = rng:NextNumber(348, 395)
	local s = rng:NextNumber(30, 70)
	ball(land, "OuterKopje", center + Vector3.new(math.cos(angle) * radius, -s * 0.2, math.sin(angle) * radius), Vector3.new(s, s * 0.7, s), i % 2 == 0 and COLORS.rock or COLORS.rockLight, Enum.Material.Sandstone, true)
end

local village = Instance.new("Folder")
village.Name = "SavannaVillage"
village.Parent = art
village:SetAttribute("ActivityType", "Social")

local mining = Vector3.new(-523, groundY, 2458)
local herbs = Vector3.new(-632, groundY, 2324)
local woodland = Vector3.new(-461, groundY, 2296)
local waterhole = center + Vector3.new(18, 0, -225)
local huntCamp = center + Vector3.new(-230, 0, 65)

path(land, "MiningTrail", center + Vector3.new(-8, 0, 52), mining, 12, -14)
path(land, "HerbalistTrail", center + Vector3.new(-62, 0, -12), herbs, 11, 16)
path(land, "WoodlandTrail", center + Vector3.new(58, 0, -20), woodland, 12, -18)
path(land, "WaterholeTrail", center + Vector3.new(18, 0, -62), waterhole, 10, 12)
path(land, "HunterTrail", center + Vector3.new(-60, 0, 28), huntCamp, 9, -16)

-- Detailed village, oriented toward the central crystal plaza.
local villageCenter = center + Vector3.new(118, groundY, 35)
local houseOffsets = {
	Vector3.new(-10, 0, 25),
	Vector3.new(28, 0, 16),
	Vector3.new(35, 0, -24),
	Vector3.new(-4, 0, -35),
}
for i, offset in ipairs(houseOffsets) do
	local position = villageCenter + offset
	local house = cloneHero("HeroHouse", village, "VillageHouse_" .. i, position, villageCenter, 1.5 + (i % 2) * 0.1)
	if not house then
		fallbackHut(village, position, villageCenter, 1.1)
	end
end
fallbackHut(village, villageCenter + Vector3.new(62, 0, 4), villageCenter, 1.05)
fallbackHut(village, villageCenter + Vector3.new(-47, 0, -6), villageCenter, 1.1)

marketStall(village, villageCenter + Vector3.new(4, 0, 3), math.rad(18), COLORS.coral)
marketStall(village, villageCenter + Vector3.new(16, 0, -8), math.rad(-25), COLORS.turquoise)

-- Cloth standards and trade goods make the village entrance readable from
-- every approach without adding collision clutter to the combat lanes.
for side = -1, 1, 2 do
	local base = villageCenter + Vector3.new(side * 18, 0, -30)
	part(village, "BannerPole", Vector3.new(0.55, 13, 0.55), CFrame.new(base + Vector3.new(0, 6.5, 0)), COLORS.bark, Enum.Material.Wood, nil, true)
	part(village, "Banner", Vector3.new(4.8, 5.5, 0.3), CFrame.new(base + Vector3.new(side * 2.15, 9.2, 0)), side < 0 and COLORS.coral or COLORS.turquoise, Enum.Material.Fabric, nil, false)
end
for i = 1, 9 do
	local angle = i * math.pi * 2 / 9
	local p = villageCenter + Vector3.new(math.cos(angle) * 24, 1.1, math.sin(angle) * 20)
	ball(village, "TradeJar", p, Vector3.new(2.2, 2.8, 2.2), i % 3 == 0 and COLORS.turquoise or (i % 2 == 0 and COLORS.gold or COLORS.coral), Enum.Material.SmoothPlastic, true)
end

local fireBase = disk(village, "FirePit", villageCenter + Vector3.new(-9, 0.55, -2), 9, 9, 1, COLORS.stone, Enum.Material.Slate, true)
local fire = ball(village, "VillageFire", fireBase.Position + Vector3.new(0, 1.3, 0), Vector3.new(2.7, 3.5, 2.7), Color3.fromRGB(255, 129, 35), Enum.Material.Neon, false)
local fireEffect = Instance.new("Fire")
fireEffect.Color = Color3.fromRGB(255, 178, 65)
fireEffect.SecondaryColor = Color3.fromRGB(207, 55, 25)
fireEffect.Size = 6
fireEffect.Heat = 7
fireEffect.Parent = fire
local fireLight = Instance.new("PointLight")
fireLight.Color = Color3.fromRGB(255, 174, 81)
fireLight.Range = 28
fireLight.Brightness = 2
fireLight.Parent = fire
label(village, villageCenter + Vector3.new(0, 0, 42), "SAVANNA VILLAGE", COLORS.gold)

-- Hero acacias provide close-up quality; lighter procedural trees fill the
-- exploration routes without multiplying imported meshes excessively.
local heroTreePositions = {
	center + Vector3.new(78, 0, -88),
	center + Vector3.new(155, 0, -70),
	center + Vector3.new(175, 0, 96),
	center + Vector3.new(-82, 0, 105),
}
for i, position in ipairs(heroTreePositions) do
	local tree = cloneHero("HeroAcacia", art, "HeroAcacia_" .. i, position, position + Vector3.new(0, 0, -1), 1.15 + i * 0.05)
	if not tree then
		lowAcacia(art, position, 1.2)
	end
end

for i = 1, 42 do
	local angle = rng:NextNumber(0, math.pi * 2)
	local radius = rng:NextNumber(125, 360)
	local position = center + Vector3.new(math.cos(angle) * radius, 0, math.sin(angle) * radius)
	if (position - mining).Magnitude > 55 and (position - waterhole).Magnitude > 55 then
		if i % 7 == 0 then
			baobab(art, position, rng:NextNumber(0.85, 1.25))
		else
			lowAcacia(art, position, rng:NextNumber(0.8, 1.2))
		end
	end
end

-- Layered savanna detail keeps the long traversal routes visually alive while
-- preserving broad sight lines for Roblox combat and mounted movement.
for i = 1, 70 do
	local angle = rng:NextNumber(0, math.pi * 2)
	local radius = rng:NextNumber(90, 365)
	local position = center + Vector3.new(math.cos(angle) * radius, 0, math.sin(angle) * radius)
	if (position - mining).Magnitude > 48 and (position - villageCenter).Magnitude > 62 then
		grassClump(art, position, rng:NextNumber(0.65, 1.2), i % 6 == 0)
	end
end
for i = 1, 11 do
	local angle = rng:NextNumber(0, math.pi * 2)
	local radius = rng:NextNumber(145, 340)
	termiteMound(art, center + Vector3.new(math.cos(angle) * radius, 0, math.sin(angle) * radius), rng:NextNumber(0.65, 1.15))
end
for i = 1, 10 do
	local angle = rng:NextNumber(0, math.pi * 2)
	local radius = rng:NextNumber(120, 350)
	rockCluster(art, center + Vector3.new(math.cos(angle) * radius, 0, math.sin(angle) * radius), rng:NextInteger(3, 6), 10, rng:NextNumber(3.5, 7))
end

-- Mining gorge aligned to the existing mining ZonePost and OreNodes.
local mineFolder = Instance.new("Folder")
mineFolder.Name = "MiningGorge"
mineFolder:SetAttribute("ActivityType", "Ore")
mineFolder.Parent = art
label(mineFolder, mining + Vector3.new(-13, 0, -7), "SUNSTONE GORGE", COLORS.gold)
rockCluster(mineFolder, mining + Vector3.new(18, 0, 20), 18, 42, 17)
rockCluster(mineFolder, mining + Vector3.new(-25, 0, 38), 14, 34, 15)
for i = 1, 8 do
	local angle = i * math.pi * 2 / 8
	local position = mining + Vector3.new(math.cos(angle) * 28, 2.5, math.sin(angle) * 28)
	local crystal = part(mineFolder, "Sunstone", Vector3.new(2.3, rng:NextNumber(5, 10), 2.3), CFrame.new(position) * CFrame.Angles(rng:NextNumber(-0.18, 0.18), angle, rng:NextNumber(-0.12, 0.12)), i % 2 == 0 and COLORS.gold or COLORS.coral, Enum.Material.Neon, nil, false)
	crystal.Transparency = 0.08
end

-- Herbalist basin aligned to the existing herb route.
local herbFolder = Instance.new("Folder")
herbFolder.Name = "HerbalistBasin"
herbFolder:SetAttribute("ActivityType", "Herbs")
herbFolder.Parent = art
label(herbFolder, herbs + Vector3.new(-12, 0, -8), "HEALER'S MEADOW", COLORS.turquoise)
for i = 1, 16 do
	local angle = rng:NextNumber(0, math.pi * 2)
	local radius = rng:NextNumber(12, 65)
	local color = i % 3 == 0 and COLORS.coral or (i % 2 == 0 and COLORS.turquoise or COLORS.gold)
	herbPatch(herbFolder, herbs + Vector3.new(math.cos(angle) * radius, 0, math.sin(angle) * radius), color)
end
for i = 1, 7 do
	local angle = i * math.pi * 2 / 7
	disk(herbFolder, "GardenBed", herbs + Vector3.new(math.cos(angle) * 38, 0.22, math.sin(angle) * 38), 18, 11, 0.35, COLORS.sandDark, Enum.Material.Ground, false)
end

-- Woodland route aligned to the existing individual WoodNodes.
local woodFolder = Instance.new("Folder")
woodFolder.Name = "AcaciaWoodland"
woodFolder:SetAttribute("ActivityType", "Wood")
woodFolder.Parent = art
label(woodFolder, woodland + Vector3.new(10, 0, 4), "ACACIA WOODLAND", COLORS.leavesLight)
for i = 1, 20 do
	local angle = rng:NextNumber(0, math.pi * 2)
	local radius = rng:NextNumber(18, 90)
	lowAcacia(woodFolder, woodland + Vector3.new(math.cos(angle) * radius, 0, math.sin(angle) * radius), rng:NextNumber(0.75, 1.12))
end
for i = 1, 20 do
	local angle = rng:NextNumber(0, math.pi * 2)
	local radius = rng:NextNumber(15, 100)
	local p = woodland + Vector3.new(math.cos(angle) * radius, 0, math.sin(angle) * radius)
	for blade = 1, 3 do
		part(woodFolder, "SavannaGrass", Vector3.new(0.25, rng:NextNumber(2, 4.5), 0.25), CFrame.new(p + Vector3.new(blade * 0.4, 1.2, 0)), COLORS.dryGrass, Enum.Material.Grass, nil, false)
	end
end

-- Watering hole and animal-viewing area.
local waterFolder = Instance.new("Folder")
waterFolder.Name = "WateringHole"
waterFolder:SetAttribute("ActivityType", "Hunt")
waterFolder.Parent = art
disk(waterFolder, "Water", waterhole + Vector3.new(0, 0.18, 0), 105, 72, 0.4, COLORS.water, Enum.Material.Glass, false).Transparency = 0.12
for i = 1, 28 do
	local angle = i * math.pi * 2 / 28
	local rx = 57 + rng:NextNumber(-3, 4)
	local rz = 40 + rng:NextNumber(-2, 4)
	local s = rng:NextNumber(3, 7)
	ball(waterFolder, "WaterRim", waterhole + Vector3.new(math.cos(angle) * rx, s * 0.2, math.sin(angle) * rz), Vector3.new(s, s * 0.55, s), i % 2 == 0 and COLORS.stone or COLORS.rock, Enum.Material.Slate, true)
end
for i = 1, 36 do
	local angle = rng:NextNumber(0, math.pi * 2)
	local rx = rng:NextNumber(42, 54)
	local rz = rng:NextNumber(29, 38)
	part(waterFolder, "Reeds", Vector3.new(0.22, rng:NextNumber(3, 6), 0.22), CFrame.new(waterhole + Vector3.new(math.cos(angle) * rx, 2.2, math.sin(angle) * rz)), COLORS.grass, Enum.Material.Grass, nil, false)
end
label(waterFolder, waterhole + Vector3.new(0, 0, 55), "MAMBA WATERING HOLE", COLORS.turquoise)

-- Hunter camp gives the wildlife loop a recognizable destination.
local huntFolder = Instance.new("Folder")
huntFolder.Name = "HunterCamp"
huntFolder:SetAttribute("ActivityType", "Hunt")
huntFolder.Parent = art
label(huntFolder, huntCamp, "HUNTER'S OUTLOOK", COLORS.coral)
for i = -1, 1 do
	local cf = CFrame.new(huntCamp + Vector3.new(i * 18, 4, 14)) * CFrame.Angles(0, math.rad(i * 12), 0)
	part(huntFolder, "Tent", Vector3.new(14, 8, 12), cf, i == 0 and COLORS.coral or COLORS.gold, Enum.Material.Fabric, nil, false)
	part(huntFolder, "TentFloor", Vector3.new(14, 0.5, 12), cf * CFrame.new(0, -3.8, 0), COLORS.bark, Enum.Material.WoodPlanks, nil, true)
end
rockCluster(huntFolder, huntCamp + Vector3.new(0, 0, -18), 9, 12, 6)

-- Dungeon facade wraps the original DungeonDoor, preserving its scripts.
local dungeonDoor = africa:FindFirstChild("DungeonDoor")
if dungeonDoor and dungeonDoor:IsA("BasePart") then
	local dungeon = Instance.new("Folder")
	dungeon.Name = "SunKingDungeon"
	dungeon:SetAttribute("ActivityType", "Dungeon")
	dungeon:SetAttribute("PartySize", 5)
	dungeon.Parent = art
	local doorPosition = dungeonDoor.Position
	rockCluster(dungeon, doorPosition + Vector3.new(0, -2, 10), 26, 34, 17)
	for side = -1, 1, 2 do
		part(dungeon, "Obelisk", Vector3.new(8, 32, 8), CFrame.new(doorPosition + Vector3.new(side * 15, 11, -2)) * CFrame.Angles(0, 0, math.rad(side * 3)), COLORS.rock, Enum.Material.Sandstone, nil, true)
		local torch = ball(dungeon, "Torch", doorPosition + Vector3.new(side * 15, 23, -6), Vector3.new(2.4, 3.4, 2.4), COLORS.gold, Enum.Material.Neon, false)
		local light = Instance.new("PointLight")
		light.Color = Color3.fromRGB(255, 145, 55)
		light.Range = 24
		light.Brightness = 2
		light.Parent = torch
	end
	part(dungeon, "Lintel", Vector3.new(38, 8, 9), CFrame.new(doorPosition + Vector3.new(0, 24, -1)), COLORS.rockLight, Enum.Material.Sandstone, nil, true)
	label(dungeon, doorPosition + Vector3.new(0, 0, -18), "DUNGEON: SUN KING'S TOMB", COLORS.gold)
end

-- Named anchors support future NPC, quest, and dungeon development without
-- changing the current systems.
local anchors = Instance.new("Folder")
anchors.Name = "GameplayAnchors"
anchors.Parent = art
local anchorData = {
	{"Village", villageCenter, "Social"},
	{"Mining", mining, "Ore"},
	{"Herbs", herbs, "Herbs"},
	{"Woodland", woodland, "Wood"},
	{"WateringHole", waterhole, "Hunt"},
	{"HunterCamp", huntCamp, "Hunt"},
}
for _, data in ipairs(anchorData) do
	local anchor = part(anchors, data[1], Vector3.new(2, 1, 2), CFrame.new(data[2]), Color3.new(1, 1, 1), Enum.Material.SmoothPlastic, nil, false)
	anchor.Transparency = 1
	anchor.CanQuery = false
	anchor:SetAttribute("ActivityType", data[3])
end

art:SetAttribute("BuildComplete", true)
print("AfricaV05 ready: village, four activity routes, watering hole, and dungeon facade built")
