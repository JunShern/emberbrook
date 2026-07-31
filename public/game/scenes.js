// scenes.js — THE scene registry, shared by play.html (launcher cards) and
// play3d.html (H developer menu). Keys can carry query flags ("ow-valley&rt=1");
// strip at '&' for any asset path. Edit HERE, never inline in either page.
//
// SCENE_REGISTRY = CURRENT content only: this is what the H developer menu offers
// and what leads the launcher. SCENE_ARCHIVE = deprecated/superseded scenes — the
// launcher renders them in one collapsed section at the bottom; the dev menu
// NEVER shows them. Deprecate by MOVING a group down, never by deleting (bundles
// stay on disk and in git).
window.SCENE_REGISTRY = {
  "▶ PLAY — the connected slice (start here)": [
    ["ow-valley&rt=1","PLAY — the connected slice","ONE CONTINUOUS GAME: spawn on the valley road at Emberbrook's gate, walk the road down the bench to Dellhollow's Valley Gate, enter the town, descend to the shelf street and walk INTO the inn, the shops, the cookhouse — and back out again. Every door and portal is derived from the map files (<b>public/world/scenegraph.json</b>); walk near one and a prompt appears — press <b>E</b>"],
  ],
  "★ DELLHOLLOW — the town (current gameplay)": [
    ["del-cine","DELLHOLLOW — the cinematic town","<b>The whole town as a sequence of FIXED pre-rendered shots</b> — the FF7/8/9 grammar this project exists for. Arrive under the new vista entrance (the whole town + river in one establishing frame), and the camera CUTS BY ITSELF as you cross from shot to shot: 17 cameras, silent 350ms fades, exact-pixel depth occlusion, every shop door prompts. Shots are DATA: <b>public/townmap/dellhollow.cameras.json</b>"],
    ["del-cottage-int","Keepers' Cottage — supper","Hearth, laid table, Mochi asleep; the Ch2 supper scene"],
    ["del-item-int","Item Shop (chandlery)","The shop archetype: counter, stuffed shelves, lamp oil and rope"],
    ["del-inn-int","Inn — The Boatmen's Rest","Common room: LOCKS: DELAYED, abandoned cards, key rack"],
    ["del-weapon-int","Weapon Shop","Grindstone, polearm barrel, forge nook"],
    ["del-armor-int","Armor Shop","Shields, mail, the harness stand"],
    ["del-cookhouse-int","Cookhouse","Open kitchen: hearth, bread oven, eel barrel"],
  ],
  "★ EMBERBROOK — the home village (blockout ratified; photoreal dressing in progress)": [
    ["emb-cine","EMBERBROOK — the cinematic village","<b>The home village as six fixed pre-rendered shots in its own Emberwake dusk</b> — the town lit by the Heartlight and Lake's fourteen lamps. Arrive up the wood road, cross Festival Square, walk into the inn, the bakery, Lake's cottage and the store (press <b>E</b> at doors). Blockout-era massing; the photoreal dressing pass is building now"],
    ["emb-townwalk","Emberbrook — free-roam explore (dev)","The full 2x village + Whisperwood arrival corridor + sealed Old Gate notch under a free follow camera. Tracks the master blend live (auto-refreshes within ~10 min of any build)"],
    ["emb-inn-int","Inn — The Ember Hearth (interior)","Parlour + inglenook + snug; Vesper's key already off the board"],
    ["emb-bakery-int","Poppy's Bakery (interior)","The wedge room: oven platform, clerestory dust shafts, honeybuns under a cloth"],
    ["emb-lake-int","Lake's Cottage (interior)","The keeper's cottage: both hooks empty — he's out on the rounds"],
    ["emb-item-int","Village Store (interior)","A farmhouse shop: warm shop, cold larder, glazed lean-to, borrow book"],
  ],
  "Developer views": [
    ["townwalk&rt=1","Dellhollow — real-time explore (dev)","The town under a free follow camera: orbit, wheel-zoom, shift-drag pan. No fixed cameras, no cuts — the cinematic card above is how the town is meant to be played"],
    ["del-boatyard","The Boatyard (detail exterior)","Slipway, hulls on the stocks, pitch kettle, boardwalk out to Lock Four's gates — detailed exterior at true town coordinates"],
  ],
};

window.SCENE_ARCHIVE = {
  "Emberbrook — legacy single-scene prototypes (superseded by the founded town)": [
    ["square3d","Festival Square (proto)","Cobblestone plaza, Heartlight, branching festival streets"],
    ["entrance3d","Village Entrance (proto)","The bending approach road into town"],
    ["lane3d","Pond Lane (proto)","Curving lane past the pond, with a branch"],
    ["forest3d","Whisperwood Trail (proto)","Winding autumn forest path + waystone"],
    ["gate3d","Sigil Gate (proto)","Courtyard with the sealed sigil gate"],
    ["interior3d","Cottage Interior (proto)","Cutaway room — hearth, table, bed"],
  ],
  "Dellhollow — legacy scaffold town (superseded by the cinematic town)": [
    ["dellhollow3d","Dellhollow (pilot)","The original scaffold river-town slice"],
    ["descent3d","The Descent","Switchback path down into the hollow"],
    ["stairs3d","Scaffold Stairs","Multi-level timber staircase — the stress test"],
    ["lockfive3d","Lock Five","The largest scaffold platform network"],
    ["cottage3d","Cliff Cottage","Cottage clinging to the cliff face"],
  ],
  // Overworld style prototype cards (rounds 1-2, ow-proto-a..h + f2) retired
  // 2026-07-30: the Valley region is canonical. Restore a card here to revisit one.
  "Chapter 3 — built, not yet vetted": [
    ["road3d","Lantern Road","The road toward Lanternstead"],
    ["lanternstead3d","Lanternstead","The lantern town square"],
    ["lanternstead-int3d","Lanternstead Interior","Interior room"],
  ],
};
