// Testa o worker inteiro contra um D1 falso (node:sqlite com o schema.sql de verdade).
import { test } from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { DatabaseSync } from 'node:sqlite';
import { trata } from '../src/index.js';
import { pontos, limpaNome } from '../src/regras.js';

function d1() {
  const db = new DatabaseSync(':memory:');
  db.exec(readFileSync(new URL('../schema.sql', import.meta.url), 'utf8'));
  return {
    prepare(sql) {
      let args = [];
      const st = db.prepare(sql);
      const api = {
        bind(...a) { args = a; return api; },
        async first() { return st.get(...args) ?? null; },
        async all() { return { results: st.all(...args) }; },
        async run() { st.run(...args); return { success: true }; },
      };
      return api;
    },
  };
}

const BASE = 'https://pato.exemplo/api/placar';
const env = () => ({ DB: d1(), PLACAR_SEGREDO: 'segredo-de-teste', ORIGENS: 'http://localhost:8765' });
const post = (url, corpo, origem) => new Request(url, { method: 'POST', body: JSON.stringify(corpo),
  headers: { 'Content-Type': 'application/json', ...(origem ? { Origin: origem } : {}), 'CF-Connecting-IP': '1.2.3.4' } });
const corrida = (extra) => ({ nivel: 'Inferno', valida: true, nome: 'Leo', tempo: 300, abates: 40, pts_abates: 4000, dano: 50,
  mortes: 1, idas_hub: 0, pontos: 999999, upgrades: { dano: 2, vida: 1 }, ...extra });

async function token(e, nivel = 'Inferno', t0 = 1_000_000) {
  return (await (await trata(post(`${BASE}/comecar`, { nivel }), e, t0)).json()).token;
}

test('fórmula igual à do jogo', () => {
  // mesma conta do teste no navegador: 150 + 1000 + (900 - 30,4833) * 10 - 110 * 20 = 7645
  assert.equal(pontos({ nivel: 'Inferno', pts_abates: 150, tempo: 30.4833, dano: 110, mortes: 0, idas_hub: 1 }), 7645);
  assert.equal(limpaNome('  <script>Léo</script>  '), 'scriptLéoscript');
  assert.equal(limpaNome(''), 'Pato');
});

test('corrida com token entra, com pontos do servidor, e aparece no placar', async () => {
  const e = env();
  const tk = await token(e);
  const r = await trata(post(BASE, corrida({ token: tk })), e, 1_000_000 + 301_000);
  const j = await r.json();
  assert.equal(r.status, 200, JSON.stringify(j));
  assert.equal(j.pontos, 4000 + 1000 + 6000 - 1000 - 500);   // ignora o "pontos" que o jogo mandou
  assert.equal(j.posicao_tempo, 1);
  const top = await (await trata(new Request(`${BASE}?nivel=Inferno&tipo=tempo`), e)).json();
  assert.equal(top.linhas.length, 1);
  assert.deepEqual(top.linhas[0].upgrades, { dano: 2, vida: 1 });
});

test('recusa token reusado, tempo mais rápido que o real, token de outra fase e corrida parcial', async () => {
  const e = env();
  const tk = await token(e);
  assert.equal((await trata(post(BASE, corrida({ token: tk })), e, 1_000_000 + 301_000)).status, 200);
  assert.equal((await trata(post(BASE, corrida({ token: tk })), e, 1_000_000 + 302_000)).status, 409);
  const tk2 = await token(e);
  assert.match((await (await trata(post(BASE, corrida({ token: tk2 })), e, 1_000_000 + 100_000)).json()).erro, /tempo real/);
  const tk3 = await token(e, 'Paraiso');
  assert.match((await (await trata(post(BASE, corrida({ token: tk3 })), e, 1_000_000 + 400_000)).json()).erro, /outra fase/);
  assert.match((await (await trata(post(BASE, corrida({ token: 'x.y' })), e, 2_000_000)).json()).erro, /token inválido/);
  assert.match((await (await trata(post(BASE, corrida({ valida: false })), e, 2_000_000)).json()).erro, /parcial/);
  assert.match((await (await trata(post(BASE, corrida({ tempo: 10 })), e, 2_000_000)).json()).erro, /mínimo/);
});

test('placar mostra o melhor de cada nome, na ordem certa', async () => {
  const e = env();
  let t = 1_000_000;
  for (const [nome, tempo] of [['Ana', 400], ['Ana', 200], ['Bia', 300]]) {
    const tk = await token(e, 'Inferno', t);
    t += 500_000;
    assert.equal((await trata(post(BASE, corrida({ nome, tempo, token: tk })), e, t)).status, 200);
    t += 61_000;   // fora da janela do limite por minuto
  }
  const top = await (await trata(new Request(`${BASE}?nivel=Inferno&tipo=tempo`), e)).json();
  assert.deepEqual(top.linhas.map((l) => [l.nome, l.tempo]), [['Ana', 200], ['Bia', 300]]);
  const pts = await (await trata(new Request(`${BASE}?nivel=Inferno&tipo=pontos`), e)).json();
  assert.equal(pts.linhas[0].nome, 'Ana');
});

test('limite de envios por minuto e origem', async () => {
  const e = env();
  let ultimo;
  for (let i = 0; i < 7; i++) {
    const tk = await token(e, 'Inferno', 1_000_000);
    ultimo = await trata(post(BASE, corrida({ token: tk })), e, 1_000_000 + 301_000 + i);
  }
  assert.equal(ultimo.status, 429);
  assert.equal((await trata(post(`${BASE}/comecar`, { nivel: 'Inferno' }, 'https://outro.site'), e)).status, 403);
  const ok = await trata(post(`${BASE}/comecar`, { nivel: 'Inferno' }, 'http://localhost:8765'), e);
  assert.equal(ok.headers.get('Access-Control-Allow-Origin'), 'http://localhost:8765');
});
