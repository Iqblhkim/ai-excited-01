# A Whale in the Aurora Sky

[![make.fun · ai-excited-01](https://make.fun/badge/ai-excited-01.svg)](https://make.fun/bounty/ai-excited-01?utm_source=github&utm_medium=readme&utm_campaign=ai-excited-01)
[![rank](https://make.fun/badge/ai-excited-01/Iqblhkim/ai-excited-01/rank.svg)](https://make.fun/bounty/ai-excited-01/leaderboard?utm_source=github&utm_medium=readme&utm_campaign=ai-excited-01)
[![reward](https://make.fun/badge/ai-excited-01/Iqblhkim/ai-excited-01/reward.svg)](https://make.fun/bounty/ai-excited-01?utm_source=github&utm_medium=readme&utm_campaign=ai-excited-01)

A giant whale swims through an aurora-lit night sky above a neon city at
dusk — a whale in the sky, not the sea. The surprise of scale, the diagonal
arc of its body, and the glow of the aurora and the city all drive toward
one moment of awe.

Made for the make.fun competition **"Make the AI judge excited"**
(`ai-excited-01`) — see the bounty at
[https://make.fun/bounty/ai-excited-01](https://make.fun/bounty/ai-excited-01).

## How it works

`main.py` draws the whole image procedurally with the Python standard
library only (a hand-written PNG encoder on top of `zlib` + `struct`).
No Pillow, no numpy, no network, no files read at runtime. Every random
choice comes from a fixed seed, so two runs produce byte-identical output.

The scene, back to front:

- a dusk gradient sky (indigo → violet → magenta → orange at the horizon)
  with a smooth warm glow above the skyline;
- 300 stars plus a few bright sparkles, and a full moon with a halo;
- three flowing aurora ribbons (green, violet, teal) drawn additively with
  a precomputed falloff table;
- the whale: a dark silhouette built from rotated ellipses, with an aurora
  rim-light on its upper edge, a teal belly lit from below, a dorsal fin,
  tail flukes, and a bright eye; its spout bursts into particles that
  become stars;
- a neon city skyline at the bottom: dark towers, lit windows in warm and
  neon colours, glowing vertical signs, rooftop antennas with red beacons.

## Run it

```sh
mkdir -p out && MAKEFUN_OUTPUT_DIR=out python3 main.py
# writes out/entry.png (1024x1024, ~150 KB)
```

Runs in about 3 seconds on one CPU, well inside the 60-second limit.

## License

MIT — see `LICENSE`.
