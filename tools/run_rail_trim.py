"""run_rail_trim.py — apply master_rail_trim.py to the open blend and save it.

Thin wrapper so the trim can be applied without command-line flags:
  Blender -b <blend> -P tools/run_rail_trim.py
"""
import sys
sys.argv = sys.argv + ["--", "--apply", "--save"]
exec(open("/Users/junshernchan/projects/multiplayer-rpg/tools/master_rail_trim.py").read())
