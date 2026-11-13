# Hub shop: upgrade catalog + trader menu (FEAT-3, system only)

## Why
Permanent upgrades are the replay hook (see `docs/revisao_design.md`, FEAT-3). The user will decide *which* upgrades exist later,
so this delivers the **system**: adding an upgrade must be a data edit in GDevelop, never new shop events or a script.

## Goals
- `trader` in the Hub opens a shop menu; coins (`moedas_total`) buy levels of upgrades, permanently.
- The menu is built entirely from a catalog stored in GDevelop variables.
- Adding/removing/retuning an upgrade = editing the catalog in the variables editor.

## Non-goals
- The trader's attacks and what killing him changes (hooks only).
- Designing or implementing new upgrades (movement upgrades, shortcuts). Effects stay wherever their mechanic lives and just read `upgrades.<id>`.
- Saving to disk, refunds/respec, the "no upgrades" leaderboard mode (SCORE-4), removing F1 debug coins (FIX-6).

## Anti-goals
- Any per-upgrade logic inside the shop events.
- Changing current values the user set (e.g. the `armas.*` globals stay as they are; current `upgrades.*` levels are kept).

## Approaches considered
- **A: catalog in variables + menu at the trader** — chosen. One list, data-only additions, supports prerequisites.
- B: physical pedestals in the Hub — tangible, but every upgrade is scene layout work and trees are awkward.
- (Dropped) one event block per upgrade — opposite of "easy to add later".

## Design
**Catalog** — global array `loja_catalogo`, one structure per entry:

| Field | Meaning |
|---|---|
| `id` | key in `upgrades` (or in `armas` when `tipo = "arma"`) |
| `nome`, `descricao` | text shown in the menu |
| `tipo` | `"upgrade"` (levels in `upgrades.<id>`) or `"arma"` (sets `armas.<id> = true`, max 1) |
| `nivel_max` | cap |
| `preco_base`, `preco_mult` | price of next level = `round(preco_base * pow(preco_mult, nivel))` |
| `requer` | optional `id` that must be at least level 1 first ("" = none) |

Seeded with the five existing stat upgrades (`cadencia`, `dano`, `recarga`, `velocidade`, `vida`), `preco_base` 50, `preco_mult` 1.6,
`nivel_max` 3 (the cap from the design review) — all editable. If `upgrades.<id>` doesn't exist for a new entry, it's treated as 0.

**Interaction** (keys not used elsewhere):
- Near `trader` (distance is a variable `loja_raio`), a hint "E" appears; **E** opens the menu, **E/Esc** closes it.
- While open, the duck's controls are disabled; `trader` plays `dialogo`.
- **W/S or mouse hover** selects a row; **Space/left click** buys.

**Menu** — a panel listing each entry: name, level `n/max`, price, description of the selected row.
Row states: affordable, too expensive (dimmed), maxed, locked by `requer` (shows what it needs).
Buying: subtract price, raise level (or set the weapon), play `aprovado` on the trader, refresh rows, re-run `AplicarUpgrades` so stats update immediately.

**The trader is a secret enemy.** Today he is in the `Inimigo` group with no events of his own, so he already hurts on touch and dies in 10 HP.
New object variable `trader_estado`: `calmo` → `hostil` → `morto`.
- **Calm** (start): no contact damage, shop available. Hitting him (bullet, explosion or punch) counts toward `paciencia`
  (hits tolerated before he snaps; default 1). When it runs out → hostile.
- **Hostile:** shop closes (menu force-closed if open), contact damage on. His attacks are a **follow-up**: an empty, labelled event group
  "Ataques do trader" is left for them.
- **Hard to kill:** his `vida`/`max_vida` raised (value is a variable; the exact number is a placeholder to tune), boss-style health bar
  shown only while hostile.
- **He kills the duck:** global `morte_trader` flag is set when the last damage came from him; on death the duck loses
  `round(moedas_total * trader_multa)` coins (`trader_multa` default 0.5). Back in the Hub he is calm again.
- **The duck kills him:** global `trader_morto = true` and an empty, labelled event group "Quando o trader morre" for the
  still-undecided consequence. Until that is decided he comes back calm on the next Hub visit, so the shop never disappears for good.

**Where it lives** — new external events `Loja`, linked from the Hub. Menu layout values (row height, colours, panel position, `loja_raio`)
are scene/object variables. Migration script `tools/t28_loja.py` only *adds* missing objects/variables/events (see `CLAUDE.md`).

## Left to the builder
- Exact visuals of the panel (reuse HUD style/fonts).
- How the menu is rendered (text objects per row created from the catalog vs. a fixed pool), as long as row count follows the catalog.
