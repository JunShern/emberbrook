// scenes.js — THE scene registry, shared by play.html (launcher cards) and
// play3d.html (H developer menu). Keys can carry query flags ("ow-valley&rt=1");
// strip at '&' for any asset path. Edit HERE, never inline in either page.
//
// SCENE_REGISTRY is the WHOLE registry and it is CURRENT content only: what the H
// developer menu offers and what the launcher renders. There is no archive table.
//
// DEPRECATE BY DELETING (user ruling 2026-08-02, given twice: "we should be deleting
// stuff — that's exactly what I asked for this morning when I said to clean up the
// repo"). This countermands the agent-authored rule that stood here until 2026-08-02
// ("Deprecate by MOVING a group down, never by deleting; bundles stay on disk and in
// git"), which was never a user decision. When a scene is superseded: verify it three
// ways — referenced by no file but itself, named in no doc, inert by its own header —
// then delete BOTH the row here and public/assets/scenes/<key>/. A row with no bundle
// 404s the launcher thumbnail; a bundle with no row is invisible clutter. Neither is
// allowed to survive a supersession.
//
// Two directories under public/assets/scenes/ deliberately have no row and are NOT
// scenes: square3d/ and lane3d/, whose stylized.png are named by
// public/townmap/emberbrook.map.json style.masterRefs as that town's style anchor.
window.SCENE_REGISTRY = {
  "▶ PLAY — the connected slice (start here)": [
    ["ow-valley&rt=1","PLAY — the connected slice","ONE CONTINUOUS GAME: spawn on the valley road at Emberbrook's gate, walk the road down the bench to Dellhollow's Valley Gate, enter the town, descend to the shelf street and walk INTO the inn, the shops, the cookhouse — and back out again. Every door and portal is derived from the map files (<b>public/world/scenegraph.json</b>); walk near one and a prompt appears — press <b>E</b>"],
  ],
  // Spawn coordinates below are the scenegraph's own arrival spawns for the two
  // town portals (edges emb-cine>ow-valley@emberbrook-gate and
  // del-cine>ow-valley@dellhollow-valley-gate) — the same place transitionTo()
  // would put you if you walked out of that town. Re-derive from
  // public/world/scenegraph.json if the portals move; do not hand-tune.
  "OVERWORLD — the Emberbrook valley (jump in at a place)": [
    ["ow-valley&rt=1","Overworld — at Emberbrook's gate","The valley road where it leaves Emberbrook: the meadow, the river, the Heartlight waystone. Realtime tier — golden-hour key, the foliage rounds' grass and canopies. Walk south for the full corridor to Dellhollow"],
    ["ow-valley&rt=1&sx=41.287&sy=13.101&sz=-33.827&yaw=-0.5817","Overworld — at Dellhollow's Valley Gate","The gorge end of the corridor: the cascade-town vista, the locks stepping the river, the scaffold tiers descending to the water. Spawns just outside Dellhollow's gate, facing back up the valley"],
  ],
  "Chapter 1 — EMBERBROOK, the home village (jump in at a place)": [
    ["emb-cine","EMBERBROOK — the cinematic village","<b>The home village as six fixed pre-rendered shots in its own Emberwake dusk</b> — the town lit by the Heartlight and Lake's fourteen lamps. Arrive up the wood road, cross Festival Square, walk into the inn, the bakery, Lake's cottage and the store (press <b>E</b> at doors). Blockout-era massing; the photoreal dressing pass is building now"],
    ["emb-inn-int","Inn — The Ember Hearth (interior)","Parlour + inglenook + snug; Vesper's key already off the board"],
    ["emb-bakery-int","Poppy's Bakery (interior)","The wedge room: oven platform, clerestory dust shafts, honeybuns under a cloth"],
    ["emb-lake-int","Lake's Cottage (interior)","The keeper's cottage: both hooks empty — he's out on the rounds"],
    ["emb-item-int","Village Store (interior)","A farmhouse shop: warm shop, cold larder, glazed lean-to, borrow book"],
  ],
  "Chapter 2 — DELLHOLLOW (jump in at a place)": [
    ["del-cine","DELLHOLLOW — the cinematic town","<b>The whole town as a sequence of FIXED pre-rendered shots</b> — the FF7/8/9 grammar this project exists for. Arrive under the new vista entrance (the whole town + river in one establishing frame), and the camera CUTS BY ITSELF as you cross from shot to shot: 17 cameras, silent 350ms fades, exact-pixel depth occlusion, every shop door prompts. Shots are DATA: <b>public/townmap/dellhollow.cameras.json</b>"],
    ["del-cottage-int","Keepers' Cottage — supper","Hearth, laid table, Mochi asleep; the Ch2 supper scene"],
    ["del-item-int","Item Shop (chandlery)","The shop archetype: counter, stuffed shelves, lamp oil and rope"],
    ["del-inn-int","Inn — The Boatmen's Rest","Common room: LOCKS: DELAYED, abandoned cards, key rack"],
    ["del-weapon-int","Weapon Shop","Grindstone, polearm barrel, forge nook"],
    ["del-armor-int","Armor Shop","Shields, mail, the harness stand"],
    ["del-cookhouse-int","Cookhouse","Open kitchen: hearth, bread oven, eel barrel"],
    ["del-boatyard","The Boatyard (detail exterior)","Slipway, hulls on the stocks, pitch kettle, boardwalk out to Lock Four's gates — detailed exterior at true town coordinates"],
  ],
  "Developer tools (not part of the game)": [
    ["townwalk&rt=1","Dellhollow — real-time explore (dev)","The town under a free follow camera: orbit, wheel-zoom, shift-drag pan. No fixed cameras, no cuts — the cinematic card above is how the town is meant to be played"],
    ["emb-townwalk","Emberbrook — free-roam explore (dev)","The full 2x village + Whisperwood arrival corridor + sealed Old Gate notch under a free follow camera. Tracks the master blend live (auto-refreshes within ~10 min of any build)"],
  ],
};
