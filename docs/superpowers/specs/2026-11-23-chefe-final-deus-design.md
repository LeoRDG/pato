# Final boss: God, the eye of light — design

Date: 2026-11-23. Project: the GDevelop game in `jogo.json` (Inferno → Purgatório → Paraíso, a duck with guns).

## Intent

The game follows the Divine Comedy and has no final boss: the Paraíso ends at "Saída no Empíreo", which just sends the duck back to the hub. The final boss is **God, a giant eye made of light**, met at the top of the Paraíso. It must stay **hard even with every upgrade maxed**, and the difficulty must come from **distinct mechanics, not more health**.

A fully upgraded duck is strong in two ways that trivialize ordinary boss design:
- mobility: +3 air jumps, dash, +30% speed, bunny hop (patterns that are hard on foot are easy to fly over);
- damage: ~1.7x damage, faster fire and reload, ricochet, piercing, electricity (any window where a boss stands and takes hits melts fast).

So the fight asks for things upgrades don't solve: being in the right place (shadows, halos), choosing targets (channelers), and keeping up with a chase.

## What the user decided

- **Shape of the fight: a chase**, inspired by the *shape* of The Binding of Isaac's Beast fight (a continuous, moving fight against a huge boss), not its content. Nothing is copied: names, art and attacks are our own.
- **The duck flies** in this fight. The **ofanim** (the "big angel") becomes a guardian mini-boss before the fight. **Wings only exist in this fight**: since the fight is an autoscroller, flying is simply how the duck moves there, and the wings are **mostly visual**.
- **A special checkpoint at the Empíreo entrance provides the wings.** Dying in the fight follows the normal rule (back to the hub, **same coin rules**), but re-entering the Paraíso puts the duck at that checkpoint.
- **Tuned for a maxed duck**: one fixed set of values; a weak build is not a target.
- **Vertical, into space**: the screen scrolls up; the background climbs from the Paraíso sky into space.
- **God is a giant eye of light**, art direction **B "the three circles"**: the eye inside three interlocking rings of light (gold, blue, rose) with a sky-blue aura, in the same pixel style as the current angels (dark outline, gold, white, blue iris). Concept sketch: `.superpowers/brainstorm/*/content/olho_b*.png`.
- **Shield channelers** (from Elder Scrolls Online raids): small angels tether the boss with beams; while any live, the boss can't be hurt.
- **GDevelop light effects**, and **the lights are the attacks**.
- **Each ring has its own mechanic.**
- **Everything happens in the Paraíso scene, no new scenes.**
- Approved animation list and attack set (below).

## Goals

1. A guardian ofanim mid-boss guarding the Empíreo, and a special checkpoint after it that provides the wings.
2. A vertical flying chase at the top of the Paraíso against God, with three ring mechanics, channelers and phases.
3. Full art: boss parts and animations, channelers, effects, background into space.
4. Lighting (GDevelop 2D lights, light obstacles, Godray/Glow/bloom effects) that carries the attacks.
5. Every tunable value is a GDevelop variable (project rule).

## Non-goals

- Permanent flight or a wings upgrade in the shop.
- A new scene (no "Empireo" scene). The `Vitoria` scene stays as it is (empty) unless the builder needs it; see "Victory".
- Changing the other realms or their bosses.

## Anti-goals (failure even if it "works")

- Beatable by staying still and holding fire, or by flying in circles with max mobility.
- Difficulty that is just HP or damage numbers.
- Anything that reads as a copy of the Beast fight (art, names, specific attacks).
- Breaking the Paraíso's normal platforming before the fight (falling, camera, enemies).
- Values hardcoded in events or scripts; migrations that overwrite the user's editor values.

## Constraints (project rules, see CLAUDE.md)

- GDevelop 5.6, `jogo.json`. Changes are made by one-time migration scripts `tools/tNN_*.py` that only **add** (never rewrite existing values, never rerun old scripts). Check `git status`/`jogo.json.autosave` for the user's edits first.
- Every number (speed, damage, timing, distance, color) is an object/scene/global variable with its initial value in `jogo.json`.
- Event organization (recent refactor): generic enemy logic in sheet `Inimigos`; Paraíso enemies in `InimigosParaiso` (one group per enemy); scene-only logic in the Paraíso scene's own events, as groups whose names say what they do; no comments.
- Shared pieces to reuse: the `Chefes` object group drives the HUD boss bar (members need `barra_dist, barra_largura, barra_rastro_vel, nome, vida, max_vida, morto`); boss poise from the cutulu (`firme`, so hits never stagger it); attack picking without repeats; phases by health thresholds (`fase2_abaixo`, `fase3_abaixo` pattern); `vida_chefe_mult`.
- Existing final-boss hook: in sheet `Portais`, "Liberação do portal final" sets scene variable `chefe_final_morto` when an `Inimigo` with `chefe_final = True` dies. Every enemy already has `chefe_final` (False). God sets it True.
- Tests in `tests/` (pytest over `jogo.json`); commit in Portuguese after each verified task.
- Art in this project is generated by Python into `assets/` in the angels' palette (see `assets/inimigos/ceu/`).

## Approaches considered

- **A. A separate "Empireo" scene** (clean lighting, camera and retries; Paraíso untouched). Not chosen: the user wants no more scenes.
- **B. The fight at the top of the Paraíso scene** — **chosen**. One continuous climb. Cost: the Paraíso must switch modes when the fight starts (lighting on, "Queda do céu" off, camera from following to scrolling, platforming to flight) and switch back cleanly on death.

## The design

### 1. Guardian ofanim and the Empíreo checkpoint

- The one ofanim in the Paraíso (~x 8192, y −2944) becomes the guardian: marked by an **instance** variable (e.g. `guardiao = True`), so ofanims placed later stay normal.
- Keeps its mechanic (closed = reflects bullets; open = vulnerable while firing eye rings) with: its own `nome`, the shared boss bar, more health (`vida_chefe_mult`), poise, and shorter/faster open windows as its health drops (thresholds and factors as variables).
- *(My call, for the user to confirm)* Killing it opens the way to the Empíreo and activates the **special checkpoint** just below the fight (a distinct, angelic checkpoint object, not a portal). The checkpoint is saved in the existing per-realm save `waypoints.Paraiso` (`ativo`, `x`, `y`), so after a death the hub portal brings the duck back there; the guardian does not need to be fought again.
- The checkpoint **provides the wings**: touching it (and every respawn at it) gives the duck the wings for the fight. The wings are visual; flight itself is the fight's movement mode (section 3).

### 2. Starting the fight (the Empíreo)

- The fight begins when the duck, with the wings from the checkpoint, reaches the current Paraíso exit area (`saida_x_min..saida_x_max`, `saida_y`). That exit no longer ends the level while God is alive; the open sky above it is the Empíreo.
- Before the guardian dies, the way up is closed (the builder picks how, e.g. a light barrier).
- On start: lighting layer on, "Queda do céu" off, camera switches to scrolling, duck switches to flight, God rises from below the screen, boss bar shows.

### 3. Flight and the chase

- Flight (only during the fight): free 8-direction movement with the same keys (A/D horizontal, W/S or jump/down vertical), dash still works; flight speed and acceleration are variables. Wings visible on the duck while flying.
- The camera rises at `subida_vel` (variable, can change per phase). The duck can't leave the top of the screen; the bottom edge is God's light: touching it burns (damage + push up, variables).
- The area is open sky with **floating fragments** (light obstacles, see Gold ring) spawned above the screen and scrolling past.
- **Background**: Paraíso sky → deep blue → black with stars as the climb goes on; each phase reaches a higher layer, so progress is visible.

### 4. God: body, parts and damage

- Built from separate parts so the pupil can track smoothly and the rings can spin at any speed: aura, eye (sclera + gold lids), iris/pupil, and the three rings (gold, blue, rose), each its own object stuck to the eye.
- Only the **pupil** takes damage, only while the eye is open and the **shield is down**. Hits never stagger it (poise). `chefe_final = True`, member of `Chefes`, name for the bar.
- Phases by health thresholds (variables):
  - **Phase 1:** Gold ring active.
  - **Phase 2:** + Blue ring.
  - **Phase 3:** + Rose ring.
  - **Final:** the three rings tear off and orbit the eye as independent hazards, each still running its mechanic, faster.
  - Phase change: rings shatter and re-form, aura and background step toward space, Godray/bloom intensify.

### 5. The three rings (the lights are the attacks)

- **Gold ring: the Gaze (sight).** The pupil is a real light source with Godray rays. It follows the duck with a delay, locks, then fires a sweeping beam of light; whatever its light reaches burns. The **floating fragments are light obstacles**: the only safety is the shadow they cast, so the duck hides behind debris that moves while the screen climbs.
- **Blue ring: the Blink (darkness).** The eye closes and the lighting layer drops near black; only a few small drifting **halos** (lights) remain, and the duck carries only a tiny light. When the eye snaps open (flash), everything outside a halo is scorched.
- **Rose ring: Love (the channelers).** Spawns small **seraph channelers** joined to the eye by rose beams (lights). While any live, the **shield** holds and the pupil is invulnerable. Periodically this ring casts **Judgment**: a long charge while channelers keep appearing; if all channelers are killed in time it is interrupted (stutter and dim); if not, it hits the duck for most of its life (variable).
- Also from the approved attack set, used by the rings as they fit: **Three Rings** (rings of light expanding from the eye, each with one gap to fly through) and the **pull** (in later phases the eye drags the duck toward it).

### 6. Animations and art (approved list)

- God: idle (aura ripples, rings turn, slow pulse), looking (pupil follows the duck), gaze charge → beam, rings spin-up → launch, blink (close, hold, snap open with flash), judgment charge + interrupted variant, shielded overlay, hurt flicker, phase change (rings shatter and re-form, aura recolors), death (rings break apart, eye closes, white flash).
- Channelers: small seraphs of the same family: idle, channel, death.
- Effects: beam, light rings, halos, shield tether, burn at the screen's bottom edge, wings pickup, wings on the duck.
- Guardian ofanim reuses its current art (maybe a tint or scale to read as "big").
- Pixel style and palette of the current angels; direction B.

### 7. Death and victory

- **Death in the fight:** normal rule: `Scene(hub)` and the usual coin rules (`moedas_perdidas`). Re-entering the Paraíso from the hub starts at the Empíreo checkpoint (`waypoints.Paraiso`), with the wings; the fight starts over from the beginning. Because the scene reloads, the fight needs no in-place reset.
- **Victory:** God dies → `chefe_final_morto` (existing hook) → the fight ends: lighting and camera return, the exit leads on (`proxima_cena`, today `Hub`/`HubParaiso`). A victory scene is out of scope.

## Left to the builder

- All numbers' initial values (balance), as variables, tuned for a fully upgraded duck (one fixed set; no scaling by upgrades): the fight should take a few minutes and a maxed run should still need several attempts.
- How the chase area is laid out (spawned fragments vs placed), exact flight feel, how the background layers are drawn.
- Light object setup (lighting layer, ambient colors per phase, which lights cast shadows), effect parameters.
- Which events go in `InimigosParaiso` (God, channelers, guardian) vs the Paraíso scene's events (fight start/stop, camera, flight, background).
- Exact frame counts and sizes of the art.
