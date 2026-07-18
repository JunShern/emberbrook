'use strict';
/* ============================================================
   ASSETS — palette, pixel-sprite compiler, portraits
   Sprites are authored as text grids and compiled to offscreen
   canvases at load. Add new art by adding new grids.
   ============================================================ */

const Palette = {
  ink: '#2b2027',
  night: '#131629',
  parchment: '#f2e4c4',
  parchDark: '#d9c49a',
  gold: '#e0a94e',
  emberGlow: '#f0a052',
  emberDeep: '#c96a2e',
  skin: '#f0c8a0',
  skinShade: '#cf9d72',
};

function makeCanvas(w, h) {
  const c = document.createElement('canvas');
  c.width = w; c.height = h;
  return c;
}

// compile a text grid + color map into a canvas (1 char = 1 px)
function px(rows, map) {
  const w = rows[0].length, h = rows.length;
  for (const r of rows) if (r.length !== w) {
    console.error('px(): ragged row', JSON.stringify(r), 'want width', w);
  }
  const c = makeCanvas(w, h), g = c.getContext('2d');
  for (let y = 0; y < h; y++) for (let x = 0; x < rows[y].length; x++) {
    const ch = rows[y][x];
    if (ch === '.' || ch === ' ') continue;
    g.fillStyle = map[ch] || '#ff00ff';
    g.fillRect(x, y, 1, 1);
  }
  return c;
}

function flipX(src) {
  const c = makeCanvas(src.width, src.height), g = c.getContext('2d');
  g.translate(src.width, 0); g.scale(-1, 1);
  g.drawImage(src, 0, 0);
  return c;
}

/* ------------------------------------------------------------
   PORTRAITS — 24×24 busts shown in the dialogue box.
   Shared legend: o ink outline · h hair · H hair shade · s skin
   S skin shade · e eye · w eye glint · m mouth · f freckle/blush
   t outfit · T outfit shade · a accent · g glow · x extra
   ------------------------------------------------------------ */
const PORTRAITS = {};

// June — cartographer. Auburn hair, side braid, teal coat, rose scarf.
PORTRAITS.june = px([
  '.......ooooooooo........',
  '.....oohhhhhhhhhoo......',
  '....ohhhhhhhhhhhhho.....',
  '...ohhhhhhhhhhhhhhho....',
  '..ohhhhhhhhhhhhhhhhho...',
  '..ohhHhhhhhhhhhhHhhho...',
  '..ohhHhhhhhhhhhhHhhho...',
  '.ohhHssssssssssssHhhho..',
  '.ohhssssssssssssssHhho..',
  '.ohHsswessssssweslHhho..',
  '.ohHsseessssssees.Hhho..',
  '.ohhssssssssssssssHhho..',
  '.ohhsfsssssssssfssHhho..',
  '..ohsssssmmmmssssHhho...',
  '..ohHsssssssssssshhho...',
  '...ohhsssssssssshhhoo...',
  '...oohhoooooooohhhoo....',
  '....ooaaaaaaaaaaoooo....',
  '...oaaaaaaaaaaaaaao.....',
  '..otttaaaattttaaattto...',
  '..ottttttttttttttttto...',
  '.otttttTTttttTTtttttto..',
  '.ottttttttttttttttttto..',
  '.oTTttttttttttttttTTto..',
], { o: Palette.ink, h: '#8a4a2c', H: '#6b3620', s: Palette.skin, S: Palette.skinShade,
     e: '#3a2a24', w: '#fff2dd', m: '#b56a58', f: '#e09a80', l: Palette.skinShade,
     t: '#3f8a7e', T: '#2e695f', a: '#c9666f' });

// Cole — lamplighter. Dark indigo coat, amber scarf, soft dark hair, warm eyes.
PORTRAITS.cole = px([
  '........oooooooo........',
  '......oohhhhhhhhoo......',
  '.....ohhhhhhhhhhhho.....',
  '....ohhhhhhhhhhhhhho....',
  '....ohhhhhhhhhhhhhho....',
  '...ohhHhhhhhhhhhhHho....',
  '...ohhssssssssssssho....',
  '...ohssssssssssssssо....'.replace('о','o'),
  '...ohsswessssssweslo....',
  '...ohsseessssssees.o....',
  '...ohssssssssssssssо....'.replace('о','o'),
  '...ohsssssssssssssso....',
  '...ohssssSmmmmSssslo....',
  '....ossssssssssssso.....',
  '....oHssssssssssHo......',
  '.....ohhsssssshhoo......',
  '.....oohhooohhhoo.......',
  '....ooaaaaaaaaaooo......',
  '...oaaaaaaaaaaaaao......',
  '..ottaaattttaaatttto....',
  '..otttttttttttttttto....',
  '.otttTTttttttTTttttto...',
  '.otttttttttttttttttto...',
  '.oTTttttttttttttTTtto...',
], { o: Palette.ink, h: '#2f2a33', H: '#211d26', s: Palette.skin, S: Palette.skinShade,
     e: '#4a3626', w: '#fff2dd', m: '#a8705c', l: Palette.skinShade,
     t: '#46527e', T: '#333d61', a: '#e0a94e' });

// Elder Rowan — grey hair, heavy brows, long beard, dusty violet robe.
PORTRAITS.rowan = px([
  '.......oooooooooo.......',
  '.....oohhhhhhhhhhoo.....',
  '....ohhhhhhhhhhhhhho....',
  '...ohhhhhhhhhhhhhhhho...',
  '...ohhhhhhhhhhhhhhhho...',
  '...ohhssssssssssssho....',
  '...ohsHHHssssHHHsslo....',
  '...ohsswessssswesslo....',
  '...ohsseessssseesslo....',
  '...ohssssssSSsssssso....',
  '...ohsSsssssssssSslo....',
  '...ohshhhhhhhhhhhslo....',
  '...ohhhhhhhhhhhhhhho....',
  '...ohhhHhhhhhhHhhhho....',
  '....ohhhhhhhhhhhhho.....',
  '....ohhhhhhhhhhhhho.....',
  '.....ohhhooooohhho......',
  '....ootttttttttttoo.....',
  '...ottttttttttttttto....',
  '..otttattttttttattto....',
  '..ottttattttttatttto....',
  '.otttttTaTTTTaTtttttо...'.replace('о','o'),
  '.otttttttttttttttttto...',
  '.oTTtttttttttttttTTto...',
], { o: Palette.ink, h: '#cfc8bd', H: '#a8a099', s: '#e8bd93', S: '#c69a70',
     e: '#33261f', w: '#fff2dd', l: '#c69a70',
     t: '#6f6288', T: '#544a6b', a: '#e0a94e' });

// Baker Poppy — round warm face, cream puff hat, terracotta dress.
PORTRAITS.poppy = px([
  '......xxxxxxxxxxx.......',
  '....xxxxxxxxxxxxxxx.....',
  '...xxxxxxxxxxxxxxxxx....',
  '...xXxxxxxXXxxxxxxXx....',
  '...xxxxxxxxxxxxxxxxx....',
  '....oxxxxxxxxxxxxxo.....',
  '....ohhhhhhhhhhhhho.....',
  '...ohhssssssssssshho....',
  '...ohsssssssssssssho....',
  '...ohsswessssswessho....',
  '...ohsseessssseessho....',
  '...ohsssssssssssssho....',
  '...ohsfssssssssfssho....',
  '...ohssssmmmmmssssho....',
  '....ossssssssssssо......'.replace('о','o'),
  '.....ossssssssssoo......',
  '.....oohhoooohhoo.......',
  '....ootttttttttttoo.....',
  '...ottttttttttttttto....',
  '..ottttaaaaaaaattttо....'.replace('о','o'),
  '..otttaaaaaaaaaatttо....'.replace('о','o'),
  '.ottttaaaaaaaaaattttо...'.replace('о','o'),
  '.otttaaaaaaaaaaaatttо...'.replace('о','o'),
  '.oTttaaaaaaaaaaaattTо...'.replace('о','o'),
], { o: Palette.ink, x: '#f2e8d0', X: '#d9cba8', h: '#a34d2c', s: '#f0c8a0', S: '#cf9d72',
     e: '#3a2a24', w: '#fff2dd', m: '#b56a58', f: '#e8987e',
     t: '#c9584a', T: '#a5433a', a: '#f2e8d0' });

// Fisher Finn — bucket hat, stubble, weathered squint, sea-blue coat.
PORTRAITS.finn = px([
  '........................',
  '......ooooooooooo.......',
  '....ooxxxxxxxxxxxoo.....',
  '...oxxxxxxxxxxxxxxxo....',
  '..oxxxxxxxxxxxxxxxxxo...',
  '..ooooooooooooooooooo...',
  '...ohsssssssssssssho....',
  '...ohsssssssssssssho....',
  '...ohswessssssswesho....',
  '...ohsseessssssee.ho....',
  '...ohsssssssssssssho....',
  '...ohsSsssssssssSsho....',
  '...ohssSSmmmmmSSssho....',
  '...ohsGsGsGsGsGsGsho....',
  '....osssssssssssso......',
  '.....ossssssssssо.......'.replace('о','o'),
  '.....oohhooоohhoo.......'.replace('о','o'),
  '....ootttttttttttoo.....',
  '...otttttttttttttttо....'.replace('о','o'),
  '..otttttattttattttto....',
  '..ottttttattatttttto....',
  '.otttttttattatttttttо...'.replace('о','o'),
  '.ottttttttttttttttttо...'.replace('о','o'),
  '.oTTttttttttttttttTTо...'.replace('о','o'),
], { o: Palette.ink, x: '#8a7448', h: '#4a3826', s: '#e0b088', S: '#bd8a60',
     e: '#33261f', w: '#fff2dd', m: '#9c6650', G: '#8a7060',
     t: '#4f7291', T: '#3a5871', a: '#c9b380' });

// Pip — small child, big eyes, messy straw hair, green smock.
PORTRAITS.pip = px([
  '........................',
  '........................',
  '.......ooooooooo........',
  '.....oohhhhhhhhhoo......',
  '....ohhhhhhhhhhhhho.....',
  '....ohHhhHhhhHhhhho.....',
  '...ohhhhhhhhhhhhhhho....',
  '...ohhsssssssssssho.....',
  '...ohsssssssssssssо.....'.replace('о','o'),
  '...ohsswwessswwesso.....',
  '...ohsseeessseeesso.....',
  '...ohsseeessseeesso.....',
  '...ohssssssssssssso.....',
  '...ohsfssssssssfsso.....',
  '....ossssmmmssssso......',
  '.....osssssssssso.......',
  '.....oohhooohhoo........',
  '.....otttttttttto.......',
  '....otttttttttttto......',
  '...ottttttttttttttо.....'.replace('о','o'),
  '...otttTTttttTTttto.....',
  '...ottttttttttttttо.....'.replace('о','o'),
  '...oTtttttttttttTto.....',
  '........................',
], { o: Palette.ink, h: '#d9b45a', H: '#b3903f', s: '#f2cea8', S: '#d1a477',
     e: '#4a3a2a', w: '#fff8e8', m: '#bd7a62', f: '#eda488',
     t: '#7a9950', T: '#5d7a3a' });

// Mara — Pip's mother. Tired kind eyes, dark bun, plum shawl.
PORTRAITS.mara = px([
  '........oooooo..........',
  '.......ohhhhhho.........',
  '......ohhhhhhhho........',
  '.....oohhhhhhhhoo.......',
  '....ohhhhhhhhhhhho......',
  '....ohhhhhhhhhhhhho.....',
  '...ohhHhhhhhhhhHhhо.....'.replace('о','o'),
  '...ohhssssssssssshо.....'.replace('о','o'),
  '...ohssssssssssssso.....',
  '...ohsswesssswessso.....',
  '...ohssSeessSSee.so.....',
  '...ohssssssssssssso.....',
  '...ohsSsssssssSssso.....',
  '...ohssssmmmmssssso.....',
  '....osssssssssssо.......'.replace('о','o'),
  '.....osssssssssoo.......',
  '.....oohhoоohhoo........'.replace('о','o'),
  '....oaaaaaaaaaaaoo......',
  '...oaaaaaaaaaaaaaao.....',
  '..oaattttttttttaaaо.....'.replace('о','o'),
  '..oattttttttttttaao.....',
  '.oaatttttttttttttaaо....'.replace('о','o'),
  '.oaTtttttttttttttTaо....'.replace('о','o'),
  '.oaaTTtttttttttTTaaо....'.replace('о','o'),
], { o: Palette.ink, h: '#3a2f33', H: '#292127', s: '#ecc099', S: '#c99a70',
     e: '#3a2a24', w: '#fff2dd', m: '#a86a58',
     t: '#8a5a6b', T: '#6b4452', a: '#5c3a52' });

// The Lanternless — hooded, faceless dark, two pale glints, empty lantern.
PORTRAITS.stranger = px([
  '........oooooooo........',
  '......oottttttttoo......',
  '.....otttttttttttto.....',
  '....otttttttttttttto....',
  '...otttTTTTTTTTTTttto...',
  '...ottTooooooooooTtto...',
  '..ottToooooooooooоTtо...'.replace(/о/g,'o'),
  '..ottoooooooooooooTto...',
  '..otToooooooooooooTto...',
  '..otToowoooooowooоTto...'.replace('о','o'),
  '..otTooooooooooooоTto...'.replace('о','o'),
  '..ottoooooooooooooTto...',
  '..otttoooooooooooTtto...',
  '...otttoooooooooTtto....',
  '...otttTooooooоTttto....'.replace('о','o'),
  '....otttTTTTTTTttto.....',
  '....otttttttttttttо.....'.replace('о','o'),
  '...otttttttttttttttо....'.replace('о','o'),
  '...otttttgggtttttttо....'.replace('о','o'),
  '..ottttttgxgttttttttо...'.replace('о','o'),
  '..ottttttgggttttttttо...'.replace('о','o'),
  '.otttttttttttttttttttо..'.replace('о','o'),
  '.otttTTttttttttTTttttо..'.replace('о','o'),
  '.oTTttttttttttttttTTtо..'.replace('о','o'),
], { o: '#0d0a12', t: '#4a4652', T: '#38343f', w: '#cfd6e8', g: '#8a8494', x: '#141020' });

// Mochi — an orange cat with opinions.
PORTRAITS.mochi = px([
  '........................',
  '........................',
  '...oo..........oo.......',
  '..ohho........ohho......',
  '..ohhho......ohhho......',
  '..ohShhoooooohhShо......'.replace('о','o'),
  '..ohhhhhhhhhhhhhhо......'.replace('о','o'),
  '.ohhhhhhhhhhhhhhhhо.....'.replace('о','o'),
  '.ohhhhhhhhhhhhhhhhо.....'.replace('о','o'),
  '.ohheehhhhhhhheehhо.....'.replace('о','o'),
  '.ohheehhhhhhhheehhо.....'.replace('о','o'),
  '.ohhhhhhsssshhhhhhо.....'.replace('о','o'),
  '.ohhhhhssmmsshhhhhо.....'.replace('о','o'),
  '.ohHhhhhsmmshhhhHhо.....'.replace('о','o'),
  '..ohhhhhhhhhhhhhho......',
  '..ohHhhhhhhhhhhHho......',
  '...ohhhhhhhhhhhho.......',
  '....oohhhhhhhhoo........',
  '...ohhhhhhhhhhhhо.......'.replace('о','o'),
  '..ohhhhHHHHHHhhhhо......'.replace('о','o'),
  '..ohhhhhhhhhhhhhhо......'.replace('о','o'),
  '..ohhHhhhhhhhhHhhо......'.replace('о','o'),
  '........................',
  '........................',
], { o: Palette.ink, h: '#d9a441', H: '#b3792f', S: '#b3792f',
     e: '#3f5c3a', s: '#f2e8d0', m: '#c98a80' });

// simple parchment-scroll icon for narration / system lines
PORTRAITS.system = px([
  '........................',
  '........................',
  '........................',
  '....oooooooooooooo......',
  '...oppppppppppppppо.....'.replace('о','o'),
  '...oppppppppppppppo.....',
  '...opdddddddddddppо.....'.replace('о','o'),
  '...oppppppppppppppo.....',
  '...opddddddddddppppо....'.replace('о','o'),
  '...oppppppppppppppo.....',
  '...opdddddddddddppо.....'.replace('о','o'),
  '...oppppppppppppppo.....',
  '...opddddddddppppppо....'.replace('о','o'),
  '...oppppppppppppppo.....',
  '...opdddddddddddppо.....'.replace('о','o'),
  '...oppppppppppppppo.....',
  '...oppppppppppppppo.....',
  '....oooooooooooooo......',
  '........................',
  '........................',
  '........................',
  '........................',
  '........................',
  '........................',
], { o: Palette.ink, p: Palette.parchment, d: '#b39a6b' });

/* ------------------------------------------------------------
   CHARACTER LOOKS — colors + accessories for the in-world
   sprites (drawn procedurally in world.js with outline+shade).
   ------------------------------------------------------------ */
const LOOKS = {
  june:     { hair: '#8a4a2c', outfit: '#3f8a7e', shade: '#2e695f', accent: '#c9666f', skin: Palette.skin, hairstyle: 'braid' },
  cole:     { hair: '#2f2a33', outfit: '#46527e', shade: '#333d61', accent: '#e0a94e', skin: Palette.skin, hairstyle: 'short' },
  rowan:    { hair: '#cfc8bd', outfit: '#6f6288', shade: '#544a6b', accent: '#e0a94e', skin: '#e8bd93', hairstyle: 'short', robe: true, beard: true, staff: true },
  poppy:    { hair: '#a34d2c', outfit: '#c9584a', shade: '#a5433a', accent: '#f2e8d0', skin: Palette.skin, hairstyle: 'bun', apron: true, hat: 'puff' },
  finn:     { hair: '#4a3826', outfit: '#4f7291', shade: '#3a5871', accent: '#c9b380', skin: '#e0b088', hairstyle: 'short', hat: 'bucket' },
  pip:      { hair: '#d9b45a', outfit: '#7a9950', shade: '#5d7a3a', accent: '#e8d5a0', skin: '#f2cea8', hairstyle: 'messy', kid: true },
  mara:     { hair: '#3a2f33', outfit: '#8a5a6b', shade: '#6b4452', accent: '#5c3a52', skin: '#ecc099', hairstyle: 'bun', shawl: true },
  stranger: { hair: '#38343f', outfit: '#4a4652', shade: '#38343f', accent: '#8a8494', skin: '#141020', cloak: true },
};

/* ------------------------------------------------------------
   IMAGE ASSETS — Ninja Adventure pack by Pixel-boy (CC0)
   https://github.com/sparklinlabs/superpowers-asset-packs
   Character sheets: 4 cols (down/up/right/left) × 7 rows of
   16×16 frames; rows 0–3 are the walk cycle.
   ------------------------------------------------------------ */
const GameImages = { tileset: new Image(), chars: {}, faces: {} };
GameImages.tileset.src = 'assets/tileset.png';

const CAST_SHEETS = { june: 6, cole: 25, rowan: 9, poppy: 16, finn: 10, pip: 17, mara: 4, stranger: 13 };
for (const [key, n] of Object.entries(CAST_SHEETS)) {
  const im = new Image();
  im.src = `assets/chars/${n}.png`;
  GameImages.chars[key] = im;
  if (key !== 'stranger') {           // the Lanternless keeps his hooded pixel portrait
    const f = new Image();
    f.src = `assets/faces/${n}.png`;
    f.onload = () => { PORTRAITS[key] = f; };
    GameImages.faces[key] = f;
  }
}

const SPEAKERS = {
  june:     { name: 'June',            color: '#3f8a7e' },
  cole:     { name: 'Cole',            color: '#e0a94e' },
  rowan:    { name: 'Elder Rowan',     color: '#8a6bae' },
  poppy:    { name: 'Baker Poppy',     color: '#c9584a' },
  finn:     { name: 'Fisher Finn',     color: '#4f7291' },
  pip:      { name: 'Pip',             color: '#7a9950' },
  mara:     { name: 'Mara',            color: '#8a5a6b' },
  stranger: { name: '???',             color: '#4a4652' },
  mochi:    { name: 'Mochi',           color: '#d9a441' },
  system:   { name: '✦',               color: '#e0a94e' },
};
