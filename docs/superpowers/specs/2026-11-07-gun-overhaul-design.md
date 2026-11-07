# Gun overhaul: base mechanics and balance

## Intent
Today every gun fires the same bullet (`projetil`, dano 12 + Random(38), straight line, dies on first hit), so the guns differ only in fire rate and pellet count. The numbers are also far apart: measured against the current objects, sustained damage per second (including reloads, every bullet hitting) is about 85 for the pistola, 400 for the doze and 390 for the minigun. The goal is three guns that each play differently, balanced against each other. Enemies are out of scope and will be balanced later.

## Goals
- Each gun has a base mechanic of its own (range, pierce, spread), not only different numbers.
- One shared damage budget so no gun is strictly better.
- All three guns stay active: doze and minigun are unlocked by default for now. The perks in `tools/t10_perks.py` (active reload, recoil jump, spin and vent) are not applied to `jogo.json` on this branch, so they are untouched.

## Non-goals / anti-goals
- No enemy changes. No new guns. No upgrade-style modifiers (burn, explode, homing); those are for later.
- Not a system where one gun is the right answer everywhere.

## The balance system
**Budget.** Every gun targets about 80-95 sustained damage per second with every bullet hitting (reload time included). A gun then trades that budget against how hard it is to land:
- Pistola: easy to land (one accurate bullet), no falloff. Gets the lowest raw number (~83).
- Doze: loses damage with distance, so its real output depends on closeness. Highest raw number (~93) and the biggest burst per magazine.
- Minigun: spread grows with heat, and the duck moves slower while firing. Raw ~76, lower in practice.

**Ammo pool.** Reserve ammo is sized so every gun holds roughly 2,800 total damage. Pistola 108 rounds, doze 32 shells, minigun 350 rounds. (Check how `pato.municao` and the ammo pickups interact with `MaxAmmo` before changing these, I have not verified that.)

## Per-gun values (starting numbers, to be tuned by play)
| | Pistola | Doze | Minigun |
|---|---|---|---|
| Role | Precision | Close burst | Sustained fire |
| Damage per bullet | 26 | 11 | 8 |
| Bullets per shot | 1 | 8 (30° fan) | 1 |
| Fire cooldown | 0.25 s | 0.7 s | 0.08 s |
| Magazine / reload | 12 / 1.0 s | 6 / 2.2 s | 100 / 2.5 s |
| Bullet range | unlimited | 450 px | 700 px |
| Damage falloff | none | 100% up to 150 px, down to 40% at max range | none |
| Pierce | 1 extra enemy | none | none |
| Spread | 3° fixed | fan only | 2° rising to 10° with heat |
| Knockback | normal | strong, strongest point-blank | weak |
| Move speed while firing | 100% | 100% | 65% |

Damage per hit becomes `dano x falloff x random(0.85 to 1.15) x mult_dano`. The old `+ Random(38)` goes away because it made weak bullets (minigun) random by 300%.

## How it gets built (my call)
- Each gun object gets variables: `dano`, `alcance`, `queda_min`, `furos`, `dispersao_min`, `dispersao_max`, `repulsao`, `vel_mov`.
- When a bullet is created, it copies those values plus its start X/Y into its own variables.
- Bullet events: delete when distance from start exceeds `alcance`; on hit, apply falloff, decrement `furos` and delete only at 0, remembering enemies already hit so one bullet never hits the same enemy twice.
- Changes go through the scripts in `tools/` (like `t10_perks.py`) rather than hand-editing `jogo.json`.

## Left to the builder
Exact event wiring, how spread rising with heat reads the existing minigun heat variables, and the visual effect for falloff (none planned).

## Open risks
- Pellet falloff and range need playtesting; 450 px and 40% are guesses.
- The pierce "already hit" list needs a per-bullet record and is the most fiddly part.
