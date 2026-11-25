// Placar global do pato: Cloudflare Worker + D1.
//   POST <base>/comecar   {nivel}            -> {token}         (no começo da corrida)
//   POST <base>           {corrida_fim, nome, upgrades, token}  -> {ok, pontos, posicao_tempo, posicao_pontos}
//   GET  <base>?nivel=Inferno&tipo=tempo|pontos&n=20           -> {nivel, tipo, linhas: [...]} (melhor de cada nome)
// <base> é a rota do worker (ex.: https://seu-dominio/api/placar).
import { REGRAS, confere, criaToken, confereToken } from './regras.js';

function json(dados, status, cors) {
  return new Response(JSON.stringify(dados), {
    status, headers: { 'Content-Type': 'application/json; charset=utf-8', ...cors },
  });
}

function cabecalhosCors(req, env) {
  const origem = req.headers.get('Origin');
  if (!origem) return {};
  const permitidas = String(env.ORIGENS || '').split(',').map((s) => s.trim()).filter(Boolean);
  const mesma = new URL(req.url).origin === origem;
  if (!mesma && !permitidas.includes(origem)) return null;
  return { 'Access-Control-Allow-Origin': origem, 'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
    'Access-Control-Allow-Headers': 'Content-Type', 'Vary': 'Origin' };
}

async function hashIp(ip, segredo) {
  const d = await crypto.subtle.digest('SHA-256', new TextEncoder().encode(`${segredo}|${ip}`));
  return [...new Uint8Array(d)].slice(0, 12).map((b) => b.toString(16).padStart(2, '0')).join('');
}

async function posicao(db, nivel, tipo, valor) {
  const sql = tipo === 'tempo'
    ? 'SELECT COUNT(*) AS n FROM (SELECT MIN(tempo) AS v FROM corridas WHERE nivel = ? GROUP BY nome) WHERE v < ?'
    : 'SELECT COUNT(*) AS n FROM (SELECT MAX(pontos) AS v FROM corridas WHERE nivel = ? GROUP BY nome) WHERE v > ?';
  const r = await db.prepare(sql).bind(nivel, valor).first();
  return (r?.n ?? 0) + 1;
}

export async function trata(req, env, agora = Date.now()) {
  const cors = cabecalhosCors(req, env);
  if (cors === null) return json({ erro: 'origem não permitida' }, 403, {});
  if (req.method === 'OPTIONS') return new Response(null, { status: 204, headers: cors });
  if (!env.PLACAR_SEGREDO) return json({ erro: 'servidor sem PLACAR_SEGREDO' }, 500, cors);
  const url = new URL(req.url);

  if (req.method === 'GET') {
    const nivel = url.searchParams.get('nivel');
    const tipo = url.searchParams.get('tipo') === 'pontos' ? 'pontos' : 'tempo';
    const n = Math.min(100, Math.max(1, Number(url.searchParams.get('n')) || 20));
    if (!REGRAS.niveis[nivel]) return json({ erro: 'fase desconhecida' }, 400, cors);
    // SQLite: com um único MIN/MAX, as outras colunas vêm da linha do melhor resultado de cada nome
    const sql = tipo === 'tempo'
      ? 'SELECT nome, MIN(tempo) AS tempo, pontos, abates, dano, mortes, idas_hub, upgrades, criado FROM corridas WHERE nivel = ? GROUP BY nome ORDER BY tempo ASC, criado ASC LIMIT ?'
      : 'SELECT nome, MAX(pontos) AS pontos, tempo, abates, dano, mortes, idas_hub, upgrades, criado FROM corridas WHERE nivel = ? GROUP BY nome ORDER BY pontos DESC, criado ASC LIMIT ?';
    const { results } = await env.DB.prepare(sql).bind(nivel, n).all();
    const linhas = results.map((r, i) => ({ ...r, posicao: i + 1, upgrades: JSON.parse(r.upgrades || '{}') }));
    return new Response(JSON.stringify({ nivel, tipo, linhas }), {
      status: 200, headers: { 'Content-Type': 'application/json; charset=utf-8', 'Cache-Control': 'public, max-age=30', ...cors },
    });
  }

  if (req.method !== 'POST') return json({ erro: 'método não permitido' }, 405, cors);
  let corpo;
  try { corpo = await req.json(); } catch { return json({ erro: 'json inválido' }, 400, cors); }

  if (url.pathname.endsWith('/comecar')) {
    if (!REGRAS.niveis[corpo?.nivel]) return json({ erro: 'fase desconhecida' }, 400, cors);
    return json({ token: await criaToken(env.PLACAR_SEGREDO, corpo.nivel, agora) }, 200, cors);
  }

  const { erro, corrida: c } = confere(corpo);
  if (erro) return json({ erro }, 400, cors);
  const tk = await confereToken(env.PLACAR_SEGREDO, corpo.token, c, agora);
  if (tk.erro) return json({ erro: tk.erro }, 400, cors);

  const ip = await hashIp(req.headers.get('CF-Connecting-IP') || 'local', env.PLACAR_SEGREDO);
  const recentes = await env.DB.prepare('SELECT COUNT(*) AS n FROM corridas WHERE ip = ? AND criado > ?').bind(ip, agora - 60000).first();
  if ((recentes?.n ?? 0) >= REGRAS.envios_por_minuto) return json({ erro: 'envios demais, espere um pouco' }, 429, cors);

  try {
    await env.DB.prepare(
      'INSERT INTO corridas (token_id, nivel, nome, tempo, pontos, abates, pts_abates, dano, mortes, idas_hub, upgrades, ip, criado) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)',
    ).bind(tk.id, c.nivel, c.nome, c.tempo, c.pontos, c.abates, c.pts_abates, c.dano, c.mortes, c.idas_hub,
      JSON.stringify(c.upgrades), ip, agora).run();
  } catch (e) {
    if (String(e).includes('UNIQUE')) return json({ erro: 'token já usado' }, 409, cors);
    throw e;
  }
  return json({
    ok: true, pontos: c.pontos,
    posicao_tempo: await posicao(env.DB, c.nivel, 'tempo', c.tempo),
    posicao_pontos: await posicao(env.DB, c.nivel, 'pontos', c.pontos),
  }, 200, cors);
}

export default { fetch: (req, env) => trata(req, env) };
