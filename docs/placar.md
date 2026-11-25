# Leaderboard: what exists and how to make it global

Each level (Inferno, Purgatorio, Paraiso) gets two boards: **fastest clear** (end to end) and **highest score**.
The in-game part is done (`tools/t199_placar.py`). What's missing is a server to collect the results, because GitHub Pages only serves static files.

---

## 1. What's already in the game

### The run (`corrida`, global)
- **Start:** entering a level from a hub starts a run (`corrida.nivel`, `ativa`).
- **Stats:** a run records time, kills, kill points, damage taken (after the difficulty scaling), deaths and hub trips.
- **End:** the run finishes at the level's final portal, or at the Empíreo exit in Paraiso.
- **Result:** the finished run is copied to `corrida_fim`.

### One session per level, paused outside it (`tools/t201_sessao_por_fase.py`)
- **Session:** a level's session runs from when the duck enters the level to when it exits through that level's final portal. That exit saves the session to the leaderboard.
- **Hub trip:** taking a mid-level portal to the hub pauses the clock (`placar.tempo_no_hub` is off).
  - Coming back through the return point resumes the session with the time it had.
  - Each trip counts in `corrida.idas_hub`, with an optional penalty `placar.pts_ida_hub` (0 by default).
- **Death:** dying doesn't end the session either. The clock pauses while the duck is in the hub, it comes back through the return point, and each death costs `placar.pts_morte`.
- **Switching levels:** each level keeps its own paused session in `corridas[level]`. Playing another level in between doesn't lose it; it resumes when the duck enters that level again.
- **HUD clock:** while the duck is in a level with a session, the clock shows the session time (`tempo_hud`).
- **Valid runs:** only a session that **started at the beginning of the level** is valid (`corrida.valida`).
  - Progress, return points and paused sessions are saved in the browser (`tools/t202_salvar_progresso.py`), so a reload continues the same session. In practice every session that reaches a final portal is valid.
  - Partial sessions are never recorded or sent.

### Score (all numbers are variables in `placar` and `placar_niveis`)
```
points = Σ kills (placar.pts_abate + enemy max HP × placar.pts_vida_inimigo)
       + placar.pts_conclusao
       + max(0, placar_niveis[level].tempo_ref − time) × placar.pts_segundo
       − damage taken × placar.pts_dano
       − deaths × placar.pts_morte
       − hub trips × placar.pts_ida_hub              (minimum 0)
```
- **Kill points scale with enemy HP,** so bosses are worth more without a separate list.
- **The time bonus uses a per-level reference time** (`tempo_ref`: Inferno 900 s, Purgatorio 900 s, Paraiso 600 s). These are guesses. Tune them from real clear times once there's data.

### Local records and the hook for a global board
- **Local records:** `recordes[level].tempo` and `.pontos` are saved in the browser (`localStorage`, key `pato_recordes`) and loaded when the game starts.
- **Submission hook:** if the global `placar_url` isn't empty, each valid finished run is sent as `POST` JSON to that URL:
  ```json
  {"jogo":"pato","nome":"<jogador_nome>","nivel":"Inferno","tempo":312.4,"pontos":8120,"abates":96,
   "pts_abates":7400,"dano":140,"mortes":1,"idas_hub":2,"valida":true,
   "recorde_tempo":true,"recorde_pontos":false,"upgrades":{"dano":2,"vida":1,"...":0}}
  ```
  The build (`upgrades`) goes with the score, so the board can show whether a score came from skill or from upgrades (see SCORE-4 in `revisao_design.md`).

### Results screen (`tools/t203_tela_de_resultado.py`)
- **When:** finishing a level session (final portal, or the Empíreo exit) goes to the `Resultado` scene instead of straight to the hub.
- **What it shows:**
  - the time and points, with the local new-record flags;
  - the points breakdown line by line;
  - the submission status, including the server's reason if it refused the run;
  - the level's two global boards (top `fim_tela.top_n`), with the player's name highlighted and an "ESTA CORRIDA" line giving this run's rank on each.
- **Fallback:** with the global board off, down, or for a partial session, the boards show the local record instead.
- **Leaving:** Space, Enter, E or a click returns to the level's hub after `fim_tela.espera` seconds.
- **Layout:** positions and sizes are in `fim_tela.*`; colors are the `ui_cor_*` variables. In windows narrower than `fim_tela.ref_w`, the layout scales down.

### Player name (`tools/t204_nome_no_hub.py`)
- **In any hub,** `nome_tela.tecla` (N) opens a panel: type the name, Enter saves, Esc cancels. It's limited to `nome_tela.max` characters, with the server's rules (letters, digits, space, `_ - .`).
- **While typing,** keys don't reach the game and the duck stands still, as in the shop.
- **A corner hint** shows the current name, or asks the player to choose one. Players who never choose still get an automatic `Pato NNNN` on their first submission.
- **The name is saved** right away with the progress.

### Board in the hub (`tools/t206_placar_no_hub.py`)
- **Portals:** the three hub portals sit side by side on the ground (Inferno, Purgatorio, Paraiso), and the ledges that held the upper two are gone.
- **Entering:** standing on a hub portal no longer enters it; you press E. Portals inside levels still enter on their own.
- **Boxes:** while the duck stands on a hub portal, two boxes appear above it: fastest times and highest points for that level.
  - Each shows the top `hub_placar.top_n`, with the player's name in gold and the player's local record at the bottom.
  - The boards are fetched when the duck steps on the portal, once per hub visit (or after `hub_placar.recarga` seconds).
  - With the global board off or down, the boxes say so and still show the local record.
- **Layout:** sizes in `hub_placar.*`; colors are the `ui_cor_*` variables.

### Still missing in the game
- **"Restart from the beginning" option at the hub portal:** it clears the level's return point. Today, a player who leaves a level midway can't do a valid run of it again until they clear it.

---

## 2. Making it global

Any score from a browser game can be faked, because the code runs on the player's machine. Every option below can only make cheating harder:
- **Check plausibility:** minimum time per level, maximum kills.
- **Recompute the score on the server** from the raw stats.
- **Limit submissions** per IP and per name.
- **Moderate by hand.**

### Option A: GDevelop Leaderboards (recommended to start)
The game already has the `LeaderboardDialog` extension. GDevelop hosts the boards for free, and they work from any domain, including github.io.

1. **Register the game:** in the GDevelop editor, sign in, then **Game dashboard → register the game** (`projectUuid` is already in `jogo.json`).
2. **Create 6 leaderboards:**
   - `Inferno – tempo` (sort ascending, shown as time), `Inferno – pontos` (sort descending).
   - The same two for Purgatorio and Paraiso.
   - Turn on "best entry per player" and set minimum/maximum score limits on each one.
3. **Store the IDs:** put the 6 leaderboard IDs in global variables, such as `placar_ids.Inferno.tempo`.
4. **Submit:** in the run-end event, add the `Save player score` action for the time board and the points board, using `corrida_fim.tempo` and `corrida_fim.pontos`.
5. **Show the boards:** use `Display leaderboard` in the hub.

- **Pros:** no server or account to maintain; in-game board display included; dashboard to delete entries; optional GDevelop player accounts.
- **Cons:** only one number per entry, so the build and stats can't be shown; validation is limited to min/max; depends on GDevelop's service.

### Option B: Cloudflare Worker + D1 (chosen, and implemented in `servidor/`)
The game's domain already runs through Cloudflare, so the Worker answers on the same site under `/api/placar`. The game requests a run token when a run starts (`tools/t200_placar_token.py`). Deploy steps are in `servidor/README.md`.
This uses the `placar_url` hook that's already there.

- **Service:** one small Worker (JavaScript) with a D1 table (SQLite):
  - `POST /placar` stores a run.
  - `GET /placar?nivel=Inferno&tipo=tempo` returns the top 50.
- **Free tier:** 100k requests per day, more than enough.
- **Validation on the server:**
  - Recompute `pontos` from the stats with the same formula. Keep the `placar` constants on the server too.
  - Reject `tempo` below the level's minimum, and kills above what the level has.
  - Only accept the game's origin (CORS limited to `https://<user>.github.io`).
  - Rate limit per IP.
- **Run token (stronger):** at the start of a run the game calls `POST /comecar` and gets a signed token with the server time. On submit, the server requires `now − start ≥ tempo`, so a fast time can't be invented after the fact.
- **The board can show** name, time, points, deaths and the build, which Option A can't.
- **Cost:** a Cloudflare account, about 100 lines of Worker code, and `wrangler deploy`.

### Option C: Supabase
- **Setup:** a Postgres table with row-level security (insert only, no update/delete) and `check` constraints for plausibility. The game writes through the REST API with the public key.
- **Stronger validation:** possible in an Edge Function.
- **Pros:** good dashboard.
- **Cons:** free projects pause after a week without activity; validation is more scattered than in a single Worker.

### Option D: Firebase (Firestore)
- **Validation:** security rules, plus App Check against simple scripts.
- **Cons:** heavier SDK in the page, and the rules language is awkward for recomputing a score.

### Not viable
**GitHub alone** (Issues, Gists, commits from the browser): it needs a token with write access inside the page, and anyone could take it.

### Recommendation
1. **Now:** Option A. It's about an hour of work in the editor, needs no infrastructure, and the extension is already installed. It also shows whether players actually use the board.
2. **When cheating shows up, or you want to show build, deaths and other details:** Option B. The in-game side is just setting `placar_url`, and the payload already carries everything the server needs to validate.
