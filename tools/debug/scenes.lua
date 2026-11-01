-- Scene list for tools/debug/warp.lua (docs/re/scenes.md). Each scene: area (5-char area script), vars and
-- flags to hold until it loads, optional from (previous area, default 1 = world map), pos {x, y}, map/event
-- (expected script names; map = false for areas without a map script), settle (frames to the proof shot).
-- Generated scenes: "<area>_<n>" for every value n of the area's progress variable (0x82 + area number) that
-- its dispatcher tests (scenes_data.lua, from gen_scenes.py), entered the normal way (flag 2 = in game).
local D = dofile("../debug/scenes_data.lua")
local S = { data = D, scenes = {} }
local ORDER = {}
local function add(name, sc) S.scenes[name] = sc; ORDER[#ORDER + 1] = name end

for _, area in ipairs(D.area_order) do
  local a = D.areas[area]
  local vals = #a.vals > 0 and a.vals or { 0 }
  for _, v in ipairs(vals) do   -- areas with no progress switch run their map in the area script (map = false)
    if area ~= "31end" then   -- the ending scene below
      -- entrance 0 keeps the player's old coordinates (docs/re/scenes.md: some maps open on an empty corner)
      local sc = { area = area, vars = { [a.var] = v }, flags = { [2] = 1 } }
      if #a.vals == 0 then sc.map = false end
      add(string.format("%s_%d", area, v), sc)
    end
  end
end
-- Visual scenes (VIS.MPS pictures + MES text): ext op `ff 27 00 <index> 00 03`, indexes 0x00-0x16
-- (docs/re/scenes.md), injected at the idle loop of 02OLB and paged through with circle.
local TOWN = { area = "02olb", vars = { [0x84] = 0 }, flags = { [2] = 1 } }
local function town(t) for k, v in pairs(TOWN) do if t[k] == nil then t[k] = v end end; return t end
for i = 0, 0x16 do
  add(string.format("vis_%02x", i), town({ run = true, inject = { 0xff, 0x27, 0, i, 0, 3 }, mash = 20,
    settle = 6000, shots = 400 }))
end
-- Ending: area 31end (VIS 01, then the credits pictures KRED00-15 through ff 2e)
add("ending", { area = "31end", map = false, mash = 30, settle = 30000, shots = 600 })
-- Field menu: cross opens it; commands 強さ 魔法 / 道具 設定 / 装備 記録 (2 columns), circle confirms
local MENU = { status = "", magic = "6 right;30 -;", items = "6 down;30 -;", config = "6 right;30 -;6 down;30 -;",
  equip = "6 down;30 -;6 down;30 -;", save = "6 right;30 -;6 down;30 -;6 down;30 -;" }
add("menu", town({ keys = "6 cross;90 -", settle = 600 }))
-- save/load slot screens (WIN02.PAD prompts, tools/gfx.py): 記録 -> Save / Load -> the slot list
add("save_slot", town({ keys = "6 cross;60 -;" .. MENU.save .. "6 circle;120 -;6 circle;180 -", settle = 900 }))
add("load_slot", town({ keys = "6 cross;60 -;" .. MENU.save .. "6 circle;120 -;6 down;30 -;6 circle;180 -",
  settle = 900 }))
-- config with every option moved right (Fast / Off / Off / Mono): the renderer colours options by byte range
add("menu_config_alt", town({ keys = "6 cross;60 -;" .. MENU.config .. "6 circle;120 -;" ..
  "6 right;30 -;6 down;30 -;6 right;30 -;6 down;30 -;6 right;30 -;6 down;30 -;6 right;60 -", settle = 1100 }))
-- the credits pictures (KRED00-15) at a shot every 60 frames
add("ending_credits", { area = "31end", map = false, mash = 30, settle = 16000, shots = 60 })
for _, k in ipairs({ "status", "magic", "items", "config", "equip", "save" }) do
  add("menu_" .. k, town({ keys = "6 cross;60 -;" .. MENU[k] .. "6 circle;120 -", settle = 700 }))
end
-- the character pages behind Status / Equip (circle picks the party member), and an equip slot's item list
add("menu_status_page", town({ keys = "6 cross;60 -;" .. MENU.status .. "6 circle;120 -;6 circle;180 -", settle = 900 }))
add("menu_magic_page", town({ keys = "6 cross;60 -;" .. MENU.magic .. "6 circle;120 -;6 circle;180 -", settle = 900 }))
add("menu_equip_page", town({ keys = "6 cross;60 -;" .. MENU.equip .. "6 circle;120 -;6 circle;180 -", settle = 900 }))
add("menu_equip_list", town({ keys = "6 cross;60 -;" .. MENU.equip .. "6 circle;120 -;6 circle;180 -;6 circle;180 -",
  settle = 1000 }))
-- Shops and inn of 02OLB01 (map script jump table 0x2042..: 0x38d6 inn, 0x39a0 item shop)
add("shop_items", town({ run = 0x39a0, keys = "6 circle;120 -", keys_at = 650, settle = 900, shots = 100 }))
add("inn", town({ run = 0x38d6, keys = "6 circle;120 -", keys_at = 650, settle = 900, shots = 100 }))
-- A choice window (op 7d at 07CSL05B 0x033d, options = data run 0xde5..): the event runs by itself on entry at
-- this progress; 7 pages (\f + op 37) come before the choice, which then stays open for the proof (width gate).
add("choice_csl", { area = "07csl", vars = { [0x89] = 5 }, flags = { [2] = 1 },
  keys = string.rep("6 circle;400 -;", 8), keys_at = 1300, settle = 5000, shots = 300 })   -- a press while a
  -- page still types only finishes it, so the presses wait for each page
-- Battles: random encounter (walk in the 21KTI cave), scripted fights (`5f 'd\bac_NN'` background,
-- `7f 'd\<enemy>'`, `81 var` = fight, result in var)
add("battle_random", { area = "21kti", map = false, flags = { [2] = 1 }, settle = 2600, shots = 200,
  keys = "200 left;200 right;200 left;200 right;200 up;200 down;200 left;200 right;200 left;200 right" })
add("battle_boss", { area = "13slp", map = false, flags = { [2] = 1 }, run = 0x04c7, settle = 1200, shots = 200 })
add("battle_event", { area = "06blk", vars = { [0x88] = 3 }, flags = { [2] = 1 }, map = "06blk04", run = 0x287f,
  settle = 1200, shots = 200 })
-- 99CMN item pickup (jump table 0x401e -> 0x4bcb): "<item> obtained." centred; the name comes from state this
-- inject does not set (blank in the JP too), so it shows the suffix line only
add("item_get", town({ run = true, inject = { 0x1d, 0x0b, 0, 2, 0, 0x01, 0x1e, 0x40 }, settle = 900, shots = 100 }))
-- 17DRL03A event 0x614: Palman's label + line written as one unit (label break is an explicit \n in the English)
add("palman_label", { area = "17drl", vars = { [0x93] = 2 }, flags = { [2] = 1 }, map = "17drl03", run = 0x5614, settle = 900, shots = 100 })
S.order = ORDER
return S
