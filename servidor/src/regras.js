// Regras do placar: a mesma fórmula de pontos do jogo (variáveis placar.* e placar_niveis.* no jogo.json) e os limites de
// plausibilidade por fase. O servidor recalcula os pontos com estes números e guarda o valor dele, não o que o jogo mandou;
// se mudar a fórmula no GDevelop, mude aqui também.
export const REGRAS = {
  pts_conclusao: 1000,
  pts_segundo: 10,
  pts_dano: 20,
  pts_morte: 500,
  pts_ida_hub: 0,
  niveis: {
    // tempo_ref: igual ao jogo. tempo_min / abates_max / pts_abates_max: limites folgados; aperte com os dados reais.
    Inferno: { tempo_ref: 900, tempo_min: 60, abates_max: 600, pts_abates_max: 80000 },
    Purgatorio: { tempo_ref: 900, tempo_min: 60, abates_max: 600, pts_abates_max: 80000 },
    Paraiso: { tempo_ref: 600, tempo_min: 45, abates_max: 300, pts_abates_max: 80000 },
  },
  nome_max: 16,
  token_validade_ms: 7 * 24 * 3600 * 1000,   // longo: a sessão de uma fase pode ficar pausada no hub
  folga_relogio_ms: 3000,     // o tempo do jogo não pode passar do tempo real desde o token (menos esta folga)
  envios_por_minuto: 6,       // por IP
};

export function pontos(c, R = REGRAS) {
  const n = R.niveis[c.nivel];
  const p = c.pts_abates + R.pts_conclusao + Math.max(0, n.tempo_ref - c.tempo) * R.pts_segundo
    - c.dano * R.pts_dano - c.mortes * R.pts_morte - c.idas_hub * R.pts_ida_hub;
  return Math.max(0, Math.round(p));
}

export function limpaNome(nome, R = REGRAS) {
  const s = String(nome ?? '').normalize('NFC').replace(/[^\p{L}\p{N} _\-.]/gu, '').replace(/\s+/g, ' ').trim();
  return s.slice(0, R.nome_max) || 'Pato';
}

// Confere o corpo enviado pelo jogo; devolve { erro } ou { corrida } com os campos já limpos.
export function confere(corpo, R = REGRAS) {
  if (!corpo || typeof corpo !== 'object') return { erro: 'corpo inválido' };
  const n = R.niveis[corpo.nivel];
  if (!n) return { erro: 'fase desconhecida' };
  if (corpo.valida !== true) return { erro: 'corrida parcial' };
  const c = { nivel: corpo.nivel, nome: limpaNome(corpo.nome, R) };
  for (const k of ['tempo', 'abates', 'pts_abates', 'dano', 'mortes', 'idas_hub']) {
    const v = Number(corpo[k]);
    if (!Number.isFinite(v) || v < 0) return { erro: `${k} inválido` };
    c[k] = k === 'tempo' ? Math.round(v * 1000) / 1000 : Math.round(v);
  }
  if (c.tempo < n.tempo_min) return { erro: 'tempo abaixo do mínimo da fase' };
  if (c.abates > n.abates_max) return { erro: 'abates demais' };
  if (c.pts_abates > n.pts_abates_max) return { erro: 'pontos de abate demais' };
  const up = corpo.upgrades && typeof corpo.upgrades === 'object' ? corpo.upgrades : {};
  c.upgrades = {};
  for (const [k, v] of Object.entries(up).slice(0, 40)) {
    const x = Number(v);
    if (/^[a-z_]{1,24}$/.test(k) && Number.isFinite(x) && x >= 0 && x <= 10) c.upgrades[k] = Math.round(x);
  }
  c.pontos = pontos(c, R);
  return { corrida: c };
}

// ---- token da corrida: assinado (HMAC-SHA256) com a hora do servidor no começo da corrida ----
const enc = new TextEncoder();
const b64 = (bytes) => btoa(String.fromCharCode(...new Uint8Array(bytes))).replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/, '');
const deb64 = (s) => Uint8Array.from(atob(s.replace(/-/g, '+').replace(/_/g, '/')), (ch) => ch.charCodeAt(0));

async function chave(segredo) {
  return crypto.subtle.importKey('raw', enc.encode(segredo), { name: 'HMAC', hash: 'SHA-256' }, false, ['sign', 'verify']);
}

export async function criaToken(segredo, nivel, agora = Date.now()) {
  const carga = b64(enc.encode(JSON.stringify({ id: crypto.randomUUID(), nivel, t0: agora })));
  const sig = await crypto.subtle.sign('HMAC', await chave(segredo), enc.encode(carga));
  return `${carga}.${b64(sig)}`;
}

// Devolve { erro } ou { id } se o token vale para esta corrida.
export async function confereToken(segredo, token, c, agora = Date.now(), R = REGRAS) {
  const [carga, sig] = String(token ?? '').split('.');
  if (!carga || !sig) return { erro: 'sem token' };
  let ok = false;
  try { ok = await crypto.subtle.verify('HMAC', await chave(segredo), deb64(sig), enc.encode(carga)); } catch { ok = false; }
  if (!ok) return { erro: 'token inválido' };
  const t = JSON.parse(new TextDecoder().decode(deb64(carga)));
  if (t.nivel !== c.nivel) return { erro: 'token de outra fase' };
  const passou = agora - t.t0;
  if (passou > R.token_validade_ms) return { erro: 'token vencido' };
  if (passou < c.tempo * 1000 - R.folga_relogio_ms) return { erro: 'tempo menor que o tempo real da corrida' };
  return { id: t.id };
}
