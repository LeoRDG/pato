# Global leaderboard (Cloudflare Worker + D1)

This serves the game's per-level leaderboards: fastest clear and highest score. The game sends finished runs here when the global `placar_url` is set in GDevelop.

| Request | What it does |
|---|---|
| `POST <base>/comecar {nivel}` | Returns a signed run token. The game asks for it when a run starts. |
| `POST <base>` | Submits a finished run. The server checks it, recomputes the score and stores it. Returns `{ok, pontos, posicao_tempo, posicao_pontos}`. |
| `GET <base>?nivel=Inferno&tipo=tempo\|pontos&n=20` | Returns the top `n` runs, showing each name's best (with deaths, hub trips and upgrades). |

## Checks on every submitted run
- **Signed token:** the run must carry a token from this server for the same level.
  - The game's time can't be shorter than the real time since the token was issued.
  - Each token is accepted only once.
  - Tokens expire after 7 days, so a level session can stay paused in the hub.
- **Score recomputed on the server:** uses the same formula as the game (`src/regras.js`). The game's own number is ignored.
- **Per-level sanity limits:** minimum time, maximum kills and maximum kill points.
- **Partial runs** (`valida: false`) are rejected.
- **Rate limit:** at most 6 submissions per minute per IP. Only a hash of the IP is stored.
- **Origin:** only accepts requests from the game's own domain and the origins listed in `ORIGENS`.

If you change the score variables (`placar.*`, `placar_niveis.*`) in GDevelop, update `src/regras.js` to match. `tests/test_placar_token.py` fails if they drift apart.

## First deploy
Run these from this folder (`servidor/`):

1. Log in to Cloudflare:
   ```
   npx wrangler login
   ```
2. Create the database:
   ```
   npx wrangler d1 create pato-placar
   ```
   Copy the `database_id` it prints into `wrangler.toml`.
3. Create the tables:
   ```
   npx wrangler d1 execute pato-placar --remote --file=schema.sql
   ```
4. Set the token secret. Paste a long random string when asked; it's never stored in the repo:
   ```
   npx wrangler secret put PLACAR_SEGREDO
   ```
5. Check `routes` and `ORIGENS` in `wrangler.toml`.
   - The game (`pato.leorods.org`) is a separate static-assets Worker (`ci/wrangler.jsonc`, deployed on every push to `main`), so the leaderboard keeps its own subdomain, `placar.leorods.org`.
   - `deploy` creates that DNS record (type Worker) and its certificate. Don't create it by hand.
   - `ORIGENS` lists the game's address, so the Worker accepts requests from it.
6. Publish:
   ```
   npx wrangler deploy
   ```
7. In GDevelop, set the global `placar_url` to `https://placar.leorods.org/api/placar`, then promote to `main` as usual.

To check that it's working, open `https://placar.leorods.org/api/placar?nivel=Inferno` in the browser. It should return `{"nivel":"Inferno","tipo":"tempo","linhas":[]}`.

## Tests and running locally
- `npm test` runs the Worker against a local stand-in for D1 (Node's built-in SQLite, Node 22.5 or newer).
- `npx wrangler dev` runs the real Worker locally. Add `http://localhost:8765` to `ORIGENS` to test with a local export of the game.

## Viewing and moderating the data
- See the latest runs:
  ```
  npx wrangler d1 execute pato-placar --remote --command "SELECT * FROM corridas ORDER BY criado DESC LIMIT 20"
  ```
- Remove a cheater:
  ```
  npx wrangler d1 execute pato-placar --remote --command "DELETE FROM corridas WHERE nome = '...'"
  ```
- The D1 dashboard on Cloudflare shows the same data.

Limitation: names aren't accounts, so anyone can submit under any name.
