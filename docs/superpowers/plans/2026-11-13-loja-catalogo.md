# Hub shop (upgrade catalog) + secret-enemy trader: implementation plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** The `trader` in the Hub opens a shop menu built from a catalog in GDevelop variables, and turns hostile when attacked
(he takes coins if he kills you; killing him sets a flag for a later consequence).

**Architecture:** All game logic lives in `jogo.json` (GDevelop 5.6). Changes are made by small **add-only** Python migration scripts in
`tools/` (one per task, run once), with shared add-only helpers in `tools/migra.py`. A new external-events sheet `Loja`, linked last in the Hub,
holds the shop and the trader logic. Each task's pytest file reads `jogo.json` and asserts the structure.

**Tech Stack:** GDevelop 5.6 project JSON, Python 3 (json, uuid), pytest.

**Spec:** `docs/superpowers/specs/2026-11-13-loja-catalogo-design.md`

## Global Constraints

- `CLAUDE.md` rules apply to every task:
  - Every tunable number is a GDevelop variable with its initial value in `jogo.json`.
  - Scripts only **add** what is missing: an existing variable keeps its current value, and existing events or objects are never rewritten except where this plan says so.
  - Never re-run old `tools/` scripts.
  - Commit messages are in Portuguese and end with `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`.
  - Stage only the files the task changed.
- GDevelop must be closed while a script runs, or it overwrites `jogo.json`.
- Before running any script: `jogo.json.autosave` currently **differs** from `jogo.json`, and both are untracked or uncommitted user work. Do not touch the autosave. If `git status` shows `jogo.json` modified, those are user edits: keep them.
- Leave the untracked `tools/t25_*`, `t26_*`, `t27_*`, `tests/test_moedas.py` and `assets/` alone, and never stage them.
- Expressions use the file's existing style: `GlobalVariable(...)`, `Variable(...)` and `obj.var`. Look up dynamic children with brackets, for example `GlobalVariable(upgrades[GlobalVariableString(loja_catalogo[Variable(loja_sel)].id)])`.
- No event in `Loja` may name a specific catalog id (`cadencia`, `dano`, …). The shop is data-driven.

## Review Focus

1. **A click while the menu is open must not shoot or punch the trader.** Clicking is how you buy. The input guard is in Task 3, tested by `test_toda_entrada_do_jogador_tem_trava`.
2. **Buying several speed levels in one visit must not compound speed (FIX-5).** Task 2, `test_velocidade_parte_da_base`.
3. **A catalog entry whose `id` isn't in `upgrades` yet** must show level 0 and become 1 when bought. Task 4, `test_loja_nao_cita_ids_do_catalogo` plus manual check M3.
4. **The coin penalty must never make `moedas_total` negative.** Task 5, `test_multa_nao_negativa`.
5. **Hitting the trader while the menu is open must close it,** and the duck's controls must come back. Task 5, `test_hostil_fecha_loja`.

---

### Task 1: Data: catalog, variables and menu objects

**Files:**
- Create: `tools/migra.py` (add-only helpers), `tools/t28_loja_dados.py`
- Test: `tests/test_loja.py`

**Interfaces:**
- Produces, in `tools/migra.py`:
  - `carrega() -> dict` and `salva(d: dict) -> None`. `salva` writes with `ensure_ascii=False, indent=2`, matching the current file formatting. Check `git diff --stat` after a no-op save.
  - `var(nome, valor) -> dict`, which also handles `str`, plus `estrutura(nome, filhos)` and `lista(nome, itens)` for arrays. Array children carry no `name`; mirror GDevelop's own array JSON.
  - `adiciona_var(lista, var) -> bool`, which adds only if the name is missing.
  - `objeto(d, nome) -> dict`, `externo(d, nome) -> list`, `anda(evs)`.
  - `C`, `A`, `E` and `comentario`, with the same shape as in `tools/t12_armas.py`.
  - `grupo(nome, eventos)`, which builds a `BuiltinCommonInstructions::Group` event.
- Produces in `jogo.json`. Every value below is the initial value of a variable:
  - **Global `loja_catalogo`** (array). Five structures, one each for `cadencia`, `dano`, `recarga`, `velocidade` and `vida`. Each has:
    - `tipo:"upgrade"`, `nivel_max:3`, `preco_base:50`, `preco_mult:1.6`, `requer:""`
    - `nome` and `descricao` in Portuguese, taken from the `AplicarUpgrades` comment. For example "Cadência" / "-15% de espera entre tiros".
  - **Global `trader_morto`:** `false`.
  - **`trader` object variables:** `paciencia:1`, `golpes:0`, `vida_vista:0`, `multa:0.5`, `dano_hostil:20`, `loja_raio:160`, `nome_barra:"Mercador"`.
    Change `estado` from `"patrulha"` to `"calmo"`. Raise `vida`/`max_vida` from 10 to 1500, but **only if they are still 10**; otherwise print a note and keep them.
  - **`pato` variables:** `na_loja:false`, `reaplicar_upgrades:false`, `velocidade_base:0`, `ultimo_agressor:""`, `moedas_perdidas:0`.
  - **`projetil_inimigo` variable:** `origem:""`.
  - **Hub scene variables:**
    - Menu state: `loja_aberta:false`, `loja_sel:0`, `loja_i:0`.
    - Layout: `loja_x:80`, `loja_y:80`, `loja_largura:620`, `loja_linha_alt:56`.
    - Row colours: `loja_cor_ok:"255;255;255"`, `loja_cor_caro:"120;120;120"`, `loja_cor_max:"240;200;80"`, `loja_cor_bloq:"200;80;80"`, `loja_cor_sel:"255;230;120"`.
  - **New global objects:**
    - `loja_painel`: Drawer, a copy of `resumo_fundo`.
    - `loja_linha`: Text, a copy of `resumo_txt` with size 28, left-aligned, plus object variable `indice:0`.
    - `loja_desc`: Text, a copy of `resumo_txt` with size 24.
    - `loja_dica`: Text, a copy of `resumo_txt` with size 28 and string `"E"`.
    - Each copy gets a new `persistentUuid`.

- [ ] **Step 1: Check for user edits.** Run `git status --short jogo.json` and `git diff --stat jogo.json`.
  Expected: no output, or user edits that you keep. Confirm GDevelop is closed.
- [ ] **Step 2: Write the failing tests** in `tests/test_loja.py`. Reuse the `JOGO`/`anda` loader pattern from `tests/test_moedas.py`.
  - `test_catalogo_tem_campos`: `loja_catalogo` is an array of 5. Each item has `id`, `nome`, `descricao`, `tipo`, `nivel_max==3`, `preco_base==50`, `preco_mult==1.6` and `requer`. The ids are exactly the five keys of global `upgrades`.
  - `test_trader_variaveis`: `trader.estado=="calmo"`, `paciencia==1`, `multa==0.5`, and `max_vida>10`.
  - `test_objetos_loja_existem`: `loja_painel`, `loja_linha` (with var `indice`), `loja_desc` and `loja_dica` exist. Every `persistentUuid` in the project is unique.
- [ ] **Step 3: Run** `pytest tests/test_loja.py -v`. Expected: 3 FAIL.
- [ ] **Step 4: Implement** `tools/migra.py` and `tools/t28_loja_dados.py`. `main()` uses only add-only helpers, plus the two guarded value changes above.
- [ ] **Step 5: Run the script, then** `pytest tests/ -v`. Expected: all PASS. Then run `git diff --stat jogo.json`; only additions plus the trader's `estado`/`vida`/`max_vida` should change.
- [ ] **Step 6: Commit.** `git add tools/migra.py tools/t28_loja_dados.py tests/test_loja.py jogo.json`, with message
  `Loja: catálogo de upgrades nas variáveis globais, variáveis do mercador e objetos do menu`.

### Task 2: Upgrades can be re-applied without compounding (FIX-5)

**Files:**
- Create: `tools/t29_reaplicar_upgrades.py`
- Test: `tests/test_loja.py` (add tests)

**Interfaces:**
- Consumes: `pato.reaplicar_upgrades` and `pato.velocidade_base` from Task 1.
- Produces: setting `pato.reaplicar_upgrades = true` re-runs *Aplicar upgrades* on the next frame. Task 4 relies on this.

Changes to the `AplicarUpgrades` → *Aplicar upgrades* event, the one with `SceneJustBegins`:
1. Insert a new event before it: `SceneJustBegins` → `pato.velocidade_base = pato.PlatformerObject::MaxSpeed()`.
2. Replace its single condition with `BuiltinCommonInstructions::Or` over `[SceneJustBegins, pato.reaplicar_upgrades == true]`.
3. Append the action `pato.reaplicar_upgrades = false`.
4. Change the MaxSpeed expression from `pato.PlatformerObject::MaxSpeed() * (1 + …)` to `pato.velocidade_base * (1 + …)`.
   **Abort with a message** if the current expression isn't exactly `pato.PlatformerObject::MaxSpeed() * (1 + pato.upg_velocidade * GlobalVariable(upgrades.velocidade))`, since that would mean the user edited it.

- [ ] **Step 1: Write the failing tests.**
  - `test_velocidade_parte_da_base`: the MaxSpeed action's expression starts with `pato.velocidade_base *`. An event with `SceneJustBegins` that sets `velocidade_base` appears before it in the same list.
  - `test_upgrades_reaplicaveis`: the event's condition is an `Or` containing `SceneJustBegins` and a `reaplicar_upgrades` check, and its actions reset `reaplicar_upgrades`.
- [ ] **Step 2: Run** them. Expected: FAIL.
- [ ] **Step 3: Implement** `tools/t29_reaplicar_upgrades.py`, using the `migra.py` helpers.
- [ ] **Step 4: Run the script, then** `pytest tests/ -v`. Expected: PASS.
- [ ] **Step 5: Commit** the script, the tests and `jogo.json`, with message `Upgrades podem ser reaplicados no meio da cena sem acumular velocidade`.

### Task 3: Duck controls are blocked while the shop is open

**Files:**
- Create: `tools/t30_trava_controles.py`
- Test: `tests/test_loja.py`

**Interfaces:**
- Consumes: `pato.na_loja` (Task 1).
- Produces: while `pato.na_loja == true`, no input event in `Jogador` fires. Task 4 sets and clears this flag.

Rule: in external events `Jogador`, every event that has an input condition gets one extra condition, `BooleanObjectVariable['pato','na_loja','False','']`. Input conditions are any condition type containing `Key`, `MouseButton` or `Gamepad`, except `F1`, which lives in `AplicarUpgrades` anyway. That's about 20 events: A, D, Space, LShift, R, 1–4, LMB, RMB and Space release.
Skip events whose input is `AnyKeyReleased`; that's the death summary. Adding a condition that is already there is a no-op.

- [ ] **Step 1: Write the failing test.** `test_toda_entrada_do_jogador_tem_trava`: for every event in `anda(Jogador)` with an input condition other than `AnyKeyReleased`, a `na_loja` `False` condition is present. Also assert the count of guarded events is greater than 0.
- [ ] **Step 2: Run** it. Expected: FAIL.
- [ ] **Step 3: Implement** `tools/t30_trava_controles.py`.
- [ ] **Step 4: Run the script and** `pytest tests/ -v`. Expected: PASS. The script prints the number of guarded events.
- [ ] **Step 5: Commit** with message `Controles do pato travam enquanto a loja está aberta`.

### Task 4: `Loja` events: hint, open/close, menu and purchase

**Files:**
- Create: `tools/t31_loja_menu.py`
- Test: `tests/test_loja.py`

**Interfaces:**
- Consumes: the variables and objects from Task 1, `pato.reaplicar_upgrades` (Task 2) and `pato.na_loja` (Task 3).
- Produces:
  - The external-events sheet `Loja`, with top-level groups named exactly `Dica`, `Abrir e fechar`, `Menu`, `Compra`, `Mercador` (empty here; Task 5 fills it) and `Barra do mercador` (empty).
  - A `Link` to `Loja`, appended as the **last** event in Hub. Its JSON shape is the same as the existing links: `{'type':'BuiltinCommonInstructions::Link','include':{'includeConfig':0},'target':'Loja'}`.

**Behaviour.** Use these names. The builder writes the events; every number comes from the variables above.

- **Dica:** when `trader.estado = "calmo"`, the trader isn't dead, `Distance(pato, trader) < trader.loja_raio` and the shop is closed, create or show `loja_dica` above the trader. Otherwise delete it.
- **Abrir e fechar:**
  - `E` just pressed while near the calm trader with the shop closed: `loja_aberta=true`, `pato.na_loja=true`, `loja_sel=0`, trader animation `dialogo`.
    Then build the menu: `loja_painel` on layer `HUD`, plus one `loja_linha` per catalog entry. Use a `Repeat GlobalVariableChildCount(loja_catalogo)` with counter `loja_i`; set `indice`, and position each row at `loja_y + indice*loja_linha_alt`. Add `loja_desc` below the rows.
  - `E` or `Escape` while open, which must not fire on the same frame it opened: delete the menu objects, `loja_aberta=false`, `pato.na_loja=false`, trader animation `idle`.
- **Menu:**
  - `W`/`S` move `loja_sel` and wrap around. Hovering a `loja_linha` sets `loja_sel = loja_linha.indice`.
  - For each row, the level is `armas[id]` (0/1) when `tipo="arma"`, otherwise `upgrades[id]`. The price is `round(preco_base * pow(preco_mult, nivel))`.
  - The row text is `nome + "  " + nivel + "/" + nivel_max + "  " + preço`. A maxed row shows "MÁX" instead of the price, and a locked row shows "precisa de " + the required entry's name.
  - Colour priority: `loja_cor_sel` if selected, else `loja_cor_bloq` if locked, `loja_cor_max` if maxed, `loja_cor_caro` if `moedas_total < preço`, otherwise `loja_cor_ok`.
  - A row is locked when `requer != ""` and `upgrades[requer] < 1`.
  - `loja_desc` shows the selected entry's `descricao`.
- **Compra:**
  - Trigger: open, and `Space` just pressed, or left mouse pressed under a `Trigger once` (so one click buys one level). The selected entry must not be maxed or locked, and `moedas_total >= preço`.
  - Effect: `moedas_total -= preço`. For `tipo="arma"`, set `armas[id] = true`; otherwise `upgrades[id] += 1`. Then trader animation `aprovado`, and `pato.reaplicar_upgrades = true`.
  - When `aprovado` ends, go back to `dialogo`.

- [ ] **Step 1: Write the failing tests.**
  - `test_hub_liga_loja_por_ultimo`: Hub's last `Link` targets `Loja`.
  - `test_loja_grupos`: `Loja` has the six groups above.
  - `test_loja_nao_cita_ids_do_catalogo`: no string in `Loja` contains `"cadencia"`, `"recarga"`, `"velocidade"`, `upgrades.` or `armas.`. The catalog ids may appear only inside brackets.
  - `test_compra_desconta_e_reaplica`: some event in `Compra` has a `moedas_total` `-` action and sets `reaplicar_upgrades` true.
  - `test_compra_exige_moedas`: that same event, or one of its ancestors, compares `moedas_total >=` a price expression.
- [ ] **Step 2: Run** them. Expected: FAIL.
- [ ] **Step 3: Implement** `tools/t31_loja_menu.py`.
- [ ] **Step 4: Run the script and** `pytest tests/ -v`. Expected: PASS.
- [ ] **Step 5: Commit** with message `Loja do Hub: menu do mercador montado a partir do catálogo, com compra de upgrades e armas`.

### Task 5: Trader as a secret enemy

**Files:**
- Create: `tools/t32_mercador_inimigo.py`
- Test: `tests/test_loja.py`

**Interfaces:**
- Consumes: the `Loja` groups `Mercador` and `Barra do mercador` (Task 4), and the Task 1 variables.
- Produces:
  - The empty, commented groups `Ataques do trader` and `Quando o trader morre`, inside `Mercador`, for the follow-ups.
  - `pato.ultimo_agressor`, which holds the object name of the last thing that damaged the duck.

**Changes:**
1. **`Loja` → `Mercador`:**
   - At scene start: `trader.vida_vista = trader.vida`.
   - While `estado = "calmo"`: if `trader.vida < trader.vida_vista`, then `golpes += 1` and `vida_vista = vida`.
   - When `golpes >= paciencia`: `estado = "hostil"`, `dano = dano_hostil`. If the shop is open, close it the same way `Abrir e fechar` does, and set `pato.na_loja=false`.
   - When the trader becomes `morto`: `trader_morto = true`, then run the `Quando o trader morre` group (comment only for now).
2. **`Barra do mercador`:** while hostile and not dead, show the `hud_boss_*` objects, set the fill width proportional to `vida/max_vida` (copy the HUD boss-bar formula), and set the `hud_boss_nome` text to `trader.nome_barra`.
3. **Contact damage only when not calm:** in `Combate` → *Dano e invencibilidade*, add the condition `StringObjectVariable['Inimigo','estado','!=','"calmo"']` to the `CollisionNP['pato','Inimigo']` event. Every `Inimigo` object declares `estado`; this was checked. Also add `SetStringObjectVariable['pato','ultimo_agressor','=','Inimigo.ObjectName()']` there, and `= projetil_inimigo.origem` in the bullet-hit event.
4. **Coin penalty:** in `Jogador` → *Morte do Pato*, add a sub-event to the death event: `pato.ultimo_agressor = "trader"` → `pato.moedas_perdidas = round(GlobalVariable(moedas_total) * trader.multa)`, then `moedas_total -= pato.moedas_perdidas`, wrapped so the result is `max(0, …)`.
   In the summary event, insert a sub-event **before** the final `SetXY` sub-event: `pato.moedas_perdidas > 0` → append `NewLine() + "O mercador levou " + ToString(pato.moedas_perdidas) + " moedas"` to `resumo_txt`.

- [ ] **Step 1: Write the failing tests.**
  - `test_contato_ignora_calmo`: the contact event has the `estado != "calmo"` condition and the `ultimo_agressor` action.
  - `test_hostil_fecha_loja`: `Mercador` contains an event that sets `estado` to `"hostil"` and, directly or in a sub-event, sets `loja_aberta` false and `na_loja` false.
  - `test_multa_nao_negativa`: the action that lowers `moedas_total` in *Morte do Pato* references `trader.multa`, and the resulting value is clamped with `max(0`.
  - `test_ganchos_vazios`: groups `Ataques do trader` and `Quando o trader morre` exist, and `trader_morto` is set true.
- [ ] **Step 2: Run** them. Expected: FAIL.
- [ ] **Step 3: Implement** `tools/t32_mercador_inimigo.py`. Abort if the target events aren't found exactly once.
- [ ] **Step 4: Run the script and** `pytest tests/ -v`. Expected: PASS.
- [ ] **Step 5: Commit** with message `Mercador é um inimigo secreto: fica hostil ao ser atacado, toma moedas ao matar o pato e marca trader_morto`.

### Task 6: Manual playtest in GDevelop and doc update

The tests only check structure, so the user has to confirm the behaviour by playing in GDevelop. The implementer hands over this checklist and waits.

- [ ] **M1:** Open the project in GDevelop with no errors in the `Loja`, `Jogador` and `Combate` event sheets.
- [ ] **M2:** In the Hub, walk to the trader and the "E" hint appears. Press E: the menu lists 5 upgrades and the duck can't move or shoot. Clicking doesn't shoot.
- [ ] **M3:** Press F1 for coins, then buy speed twice. Coins go down and the level shows 2/3. Speed rises once per level and doesn't compound. Add a test catalog entry with a new id in GDevelop: it shows 0/3 and can be bought.
- [ ] **M4:** Shoot the calm trader: he turns hostile, his bar appears and the shop is closed. Touching him hurts. Let him kill you: the summary says how many coins he took, and back in the Hub he's calm again.
- [ ] **M5:** Kill the trader and confirm `trader_morto` is true in the debugger.
- [ ] **Step: Doc.** In `docs/revisao_design.md`, add one line under FEAT-3 pointing to this plan and the spec. Commit it with message `Revisão de design: FEAT-3 aponta para o plano da loja`.
