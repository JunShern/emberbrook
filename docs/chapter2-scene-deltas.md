# Chapter 2 scene deltas — painted reality vs. script §(a)

The Dellhollow backdrops are final. Where the paintings landed POIs at different
coordinates than the screenplay's sketch, THESE values override the doc. The
engine implementation must use the coordinates below; everything not listed
landed where the script said. All masks are baked and BFS-verified between every
POI and exit mouth (descent 11/11, dellhollow 15/15, lockfive 8/8, landing 5/5).

## descent
- Road top entry: road emerges from the forest at ~(650, 120) (not top-left
  (120,140)); the forest floor is walkable, so the denied north exit still works.
- Hairpin 1: (1130,300) → (940, 200). Hairpin 2: (240,520) → (130, 470).
- Chart-halt boulder: now the slab spanning (300–450, 205–285); interact (420, 320).
- Stranger's far-rim mark: (1270,210) → (1250, 80), on the painted far-rim road.
  No glint was painted — stage the "catch of light" as a cutscene sparkle effect.
- Empty lamp bracket: free-standing bracket post at (660, 95), interact base
  (660, 170). Small ambiguous hanging ring — judged not Order-readable.
- Vista parapet: as doc'd (672, 730).

## dellhollow
- **EXIT MOVE (required):** the doc's north exit zone (100,0,260,80) is open
  water in the painting. The route to `descent` is the rope bridge exiting the
  WEST edge: zone ~{x:0, y:90, w:60, h:70}; and the descent→dellhollow spawn
  moves (210,165) → **(210, 110)** (on the bridge deck).
- Banks connect via a Lock One gate-top crossing corridor at (580–680, 130–350);
  the painted gate timbers carry it visually.
- Pumpkin barge: (270,320) → (265, 240); interact stays (300, 380).
- Lock 1 (470,260) → (620, 265) · Lock 2 (760,400) → (890, 400) ·
  Lock 3 (1020,540) → (750, 540) · waterwheel 2 (880,430) → (625, 420).
- Tally beam interact: (880,340) → (880, 400).
- Crane: (820,440) → (805, 235), approach (860, 255).
- Guildhall door: (1080,420) → (1058, 270), approach (1055, 300).
- Notice board: (1010,480) → (985, 255), approach (1025, 270).
- Lamp-pole (Pell's station): (620,560) → (528, 470).
- Eel-stall interact: (430, 540) as doc'd. Lockfive↔dellhollow exit zones and
  spawns (1230,640)/(1230,240) work as doc'd.

## lockfive
- The Tenant is PAINTED INTO the backdrop (head raised at the surface, pale
  clouded eye toward viewer, one easy coil). Eye POI: (560,540) → (555, 495).
  The keyed tenant-head/coil cutout pieces in assets/characters/tenant/ are for
  cutscene moments only if needed — never double them against the painted eel.
- Sluice grate: (180,430) → (320, 370); interact (310,680) → (330, 620).
- Flume mouth: (1120,280) → (920, 190).
- Winch L: (990,520) → (975, 385), approach (950, 480).
  Winch R: (1200,560) → (1080, 400), approach (1090, 480).
- Hung (shrouded) boat: (600,220) → (645, 240).
- Stair landing: (1240,200) → (1180, 300). Exit zone + spawn (1230,240) as doc'd.
- Work-lanterns painted at ~(240, 545) and (900, 535).
- Baked coverage is 18% (below Gate B's 25% floor) by scene nature: pool and
  walls dominate. Accepted deviation.

## landing
- Portage stair foot: (1050,420) → (1060, 330).
- Boat-moor stage mark: ~(560, 560) against the quay steps.
- Cutscene-only: generous flat quay mask, no exits. Coverage 22%, accepted.
