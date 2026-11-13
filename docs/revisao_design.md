# Design review: fixes and features

Review of `jogo.json` as of commit `dce64b5`. Plan: three worlds (Hell, Purgatory, Heaven), each with a level and a boss, a Hub shop between them, and a Hotline Miami-style score with a leaderboard.

Every new number below must be a GDevelop variable from the start (see `CLAUDE.md`).

---

## Current state

- **Working:** movement feel (jump buffer, coyote time, short hop, heavy fall), 4 weapons with their own falloff, spread and recoil, punch launch (`coice_*`), about 20 enemy types with telegraphed attacks, HUD, coin drops.
- **Missing or placeholder:**
  - [ ] `Menu` jumps straight to the Hub.
  - [ ] `Vitoria` is empty.
  - [ ] Hub exit is just `PosX(pato) > 2600`.
  - [ ] `trader` in the Hub has no shop logic. Upgrades are applied (`AplicarUpgrades`), but nothing sells them.
  - [ ] No `Boss` scene, but the death code still checks `CurrentSceneName() = "Boss"`.
  - [ ] Boss has only one attack: the curved jump (external events `Boss`).
  - [ ] `Inferno` is a test line of one enemy of each type, with no level design.
  - [ ] Leaderboard extension (`LeaderboardDialog`) is installed but never called.

---

## Fixes

### FIX-1: Getting hit doesn't push the duck away (high)
- **Where:** `Combate` → *Dano e invencibilidade*.
- **Problem:** contact and bullet damage only call `SimulateJumpKey`. On the ground that's a small vertical hop. In the air it does nothing. There's no horizontal push, so the duck can stay inside an enemy and take hit after hit.
- **Fix:** push away from the attacker (sign of `pato.CenterX() - Inimigo.CenterX()`). New `pato` variables: `dano_empurrao_x`, `dano_empurrao_y`.

### FIX-2: Every enemy hurts on touch in every state (high)
- **Where:** `Combate` → *Dano e invencibilidade* (`CollisionNP(pato, Inimigo)`).
- **Problem:** enemies stunned by the punch (`estado = "dano"`) still deal contact damage. In a close-range punching game, the enemy you just knocked back hurts you.
- **Fix:** skip contact damage while the enemy's `estado` is `"dano"`, and/or while the punch is active (`soco_duracao`). Make it a toggle variable.

### FIX-3: Coins and upgrades persist through death (high, blocks the leaderboard)
- **Where:** `moedas_total` (global), `upgrades` (global), `Combate` → *Moeda* → *Coleta*.
- **Problem:** with permanent coins and stat upgrades, the score rewards grinding instead of skill.
- **Fix:** see the "Run economy" section under Score.

### FIX-4: Progress % only works for left-to-right levels (medium)
- **Where:** `Jogador` → *Morte do Pato* (`ultima_run.progresso`, from `inicio.X` to `safezone.X`).
- **Problem:** gives wrong numbers for vertical levels (Heaven) or room-based layouts.
- **Fix:** use rooms or checkpoints cleared / total.

### FIX-5: Speed upgrade compounds (low)
- **Where:** `AplicarUpgrades`: `MaxSpeed = MaxSpeed() * (1 + ...)`.
- **Problem:** the other upgrades start from a base value. Speed multiplies itself, so it would compound if the duck ever persisted between scenes or the event ran twice.
- **Fix:** add `pato.velocidade_base` and calculate from it.

### FIX-6: F1 debug coins (medium, before release)
- **Where:** `AplicarUpgrades` → *Debug* (`f1_moedas`).
- **Fix:** remove it, or have it set a `run_invalida` flag that blocks leaderboard submission.

### FIX-7: Small cleanups (low)
- [ ] Empty event `boss.vida <= 0` inside `Combate` → *Morte do Inimigo*.
- [ ] *Troca de Arma* comment says 1/2/3, but there are 4 weapons (`lanca` on 4).
- [ ] No mouse-wheel or Q quick-swap, which matters with 4 weapons.
- [ ] Death code references a `Boss` scene that doesn't exist.

---

## Features

### FEAT-1: Shared room/arena logic (prerequisite for every level)
- Each level is a chain of arena rooms: doors lock, waves spawn, doors open.
- Rooms give natural checkpoints and readable scoring, as Hotline Miami's floors do.
- Shared external events (for example `Salas`), so all three worlds use the same logic.
- Variables: waves per room, spawn delay, door timing.

### FEAT-2: Progression loop
- Flow: Menu → Hub → Level → Hub (shop) → Boss → Hub → next world → Victory.
- A global `fase_atual` decides where the Hub door leads.
- Fill in `Menu` and `Vitoria`.

### FEAT-3: Hub shop
- Make `trader` interactive: buy upgrades and weapons (`upgrades.*`, `armas.*`).
- Prices as variables.

### FEAT-4: Bosses with 3 phases
- Rule: each phase adds one new pattern with a clear warning, and the phase shows on the existing boss bar (`hud_boss_*`).
- **Hell boss:** reuse the unused `diabo`, `demonio_velho` or `gigante_infernal` sprites.
  1. The current curved jump.
  2. Fire waves (reuse the `caveira_gigante` fire logic).
  3. The arena floor turns to lava.
- **Purgatory boss:** a mirror "pure" duck that copies your current weapon.
- **Heaven boss:** a giant ofanim with rotating bullet rings and weak points you reach by punch-launching.

### FEAT-5: The three worlds

| | Hell (Inferno) | Purgatory | Heaven |
|---|---|---|---|
| Teaches | Shoot, punch, punch-launch | Mastery under pressure | Everything, mostly vertical |
| Level gimmick | Lava, collapsing bridges, wide arenas | Grey fog rising from below, crumbling platforms, enemies that rise once unless finished with a punch | Cloud platforms you can jump up through, wind lanes, long falls |
| Enemies | Current roster | Grey versions plus wardens/judges | `assets/anjos`: ofanim, roda_anjo, serafim |

**Design pillar:** the punch launch is the game's identity. Every level should require moving by punching walls and floors, and the score should reward it.

### FEAT-6: Combat feel
- [ ] Hitstop on kills and punch hits (`hitstop_tempo`, about 0.04–0.06 s).
- [ ] Screen shake on explosions and boss slams (intensity as a variable).

---

## Score system (Hotline Miami style)

### SCORE-1: Collected during play
- **Kill points:** new per-enemy variable `pontos`, next to `qtd_moedas`.
- **Combo:** each kill within `combo_janela` seconds (about 2–3 s) raises the multiplier. Getting hit resets it. Show it big on the HUD.
- **Style bonuses (one variable each):**

| Bonus | Condition |
|---|---|
| Punch kill | kill with `soco` |
| Air kill | kill while the duck is in the air |
| Mobility | kill within N seconds after a punch launch |
| Explosion multi-kill | 2+ kills from one explosion |
| Boldness | kill an enemy in `estado = "preparar"` |

### SCORE-2: End-of-level tally screen
- Shown in the `Vitoria` scene or a new `Resultado` scene.
- Lines: `Kills · Combo · Time bonus · Flexibility (weapons used) · Mobility · No-hit rooms → Total → Grade (D…S)`.
- Each line counts up with a sound.
- Grade thresholds are variables per level.

### SCORE-3: Death rule
- Dying restarts the current room and resets that room's score, the same way Hotline Miami restarts the floor.
- The clock keeps running, so deaths cost you through the time bonus instead of a flat penalty.

### SCORE-4: Run economy (leaderboard fairness)
- **Main board: full run.** Starting a new run resets coins and upgrades. Coins are spent in the Hub only between levels during that run.
- **Permanent unlocks, if any:** options only (weapons, cosmetics), never stat boosts.
- **Unspent coins add to the score.** The player chooses between buying power and banking points.
- **Per-level boards:** secondary, for practice.

### SCORE-5: Leaderboard submission
- Use GDevelop's built-in leaderboards (the `LeaderboardDialog` extension is already installed).
- They are client-side, so add plausibility caps (for example, maximum points per second) and never submit runs flagged `run_invalida`.

---

## Suggested order

1. [ ] FIX-1, FIX-2 (knockback, contact damage)
2. [ ] FEAT-1, FEAT-2 (rooms, progression loop)
3. [ ] Build Hell properly with the current roster, plus its boss (FEAT-4)
4. [ ] SCORE-1, SCORE-2, SCORE-3
5. [ ] FEAT-3 + SCORE-4 (shop, run economy)
6. [ ] FIX-6 + SCORE-5 (leaderboard)
7. [ ] Purgatory, then Heaven
