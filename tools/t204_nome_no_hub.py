"""Tarefa 204: o jogador escolhe o nome do placar no hub.
- Em qualquer hub, a tecla nome_tela.tecla (N) abre um painel: o jogador digita o nome, Enter salva e Esc cancela.
  Backspace apaga e colar (Ctrl+V) também funciona. O nome tem no máximo nome_tela.max letras e segue as mesmas regras do servidor
  (letras, números, espaço, _ - .); nome vazio não troca o nome atual.
- Enquanto o painel está aberto, as teclas não chegam ao jogo (W/A/S/D não mexem o pato, X não mata) e o pato fica parado
  como na loja (pato.na_loja). Não abre com a loja aberta nem com o pato morto.
- No canto da tela, uma dica mostra o nome atual ("N  NOME: ...") ou pede para escolher um ("N  ESCOLHA SEU NOME PARA O PLACAR").
- O nome vai para jogador_nome e é salvo na hora junto com o progresso (t202).
- Posições, tamanhos e tempos em nome_tela.* (dica em fração da tela); cores ui_cor_*. Em janela mais estreita que nome_tela.ref_w,
  os tamanhos em pixels encolhem na mesma proporção.
- Objetos próprios (nome_txt, nome_painel) para não misturar com os textos da loja (ui_txt).
Rodar uma vez:  python3 tools/t204_nome_no_hub.py
"""
import copy
from gd_mig import *

TELA = [
    ('tecla', 'n'), ('max', 16), ('ref_w', 1920),
    ('dica_x', 0.015), ('dica_y', 0.965), ('tam_dica', 22),
    ('painel_w', 820), ('painel_h', 300), ('painel_borda', 4), ('painel_opacidade', 240),
    ('tam_titulo', 34), ('tam_nome', 60), ('tam_ajuda', 22), ('gap', 34), ('pisca', 0.5),
]

NOME = [
    'try {',
    '  // Nome do jogador (t204): N abre o painel no hub, Enter salva, Esc cancela. Números em nome_tela.*, cores ui_cor_*.',
    '  const jogo = runtimeScene.getGame();',
    '  const V = jogo.getVariables();',
    '  const T = V.get("nome_tela");',
    '  const W = jogo.getGameResolutionWidth();',
    '  const H = jogo.getGameResolutionHeight();',
    '  const escala = Math.min(1, W / T.getChild("ref_w").getAsNumber());',
    '  const crus = ["max", "ref_w", "dica_x", "dica_y", "painel_opacidade", "pisca"];',
    '  const n = (k) => T.getChild(k).getAsNumber() * (crus.includes(k) ? 1 : escala);',
    '  const cor = (k) => V.get(k).getAsString();',
    '  const limpa = (s) => String(s).normalize("NFD").replace(/[\\u0300-\\u036f]/g, "").toUpperCase();',
    '  // mesmas regras do servidor (limpaNome em servidor/src/regras.js)',
    '  const valido = (c) => /^[\\p{L}\\p{N} _\\-.]$/u.test(c);',
    '  const N = jogo.__nome || (jogo.__nome = { aberto: false, texto: "", t: 0, cena: null, engolidas: new Set() });',
    '  N.cena = runtimeScene;',
    '  const pato = () => { const p = N.cena && N.cena.getObjects("pato"); return p && p[0]; };',
    '  if (!N.instalado) {',
    '    N.instalado = true;',
    '    N.fecha = (salva) => {',
    '      try {',
    '        if (salva) {',
    '          const nome = N.texto.normalize("NFC").replace(/\\s+/g, " ").trim().slice(0, V.get("nome_tela").getChild("max").getAsNumber());',
    '          if (nome) {',
    '            V.get("jogador_nome").setString(nome);',
    '            if (jogo.__save && jogo.__save.salva) jogo.__save.salva();',
    '          }',
    '        }',
    '        const p = pato();',
    '        if (p) p.getVariables().get("na_loja").setBoolean(N.loja_antes);',
    '      } catch (e) {}',
    '      N.aberto = false;',
    '    };',
    '    const noHub = () => jogo.getSceneStack().getCurrentScene() === N.cena && N.quadro === N.cena.getTimeManager().getTimeFromStart();',
    '    window.addEventListener("keydown", (ev) => {',
    '      try {',
    '        if (ev.ctrlKey || ev.metaKey || ev.altKey) return;',
    '        if (!N.aberto) {',
    '          const tecla = V.get("nome_tela").getChild("tecla").getAsString().toLowerCase();',
    '          if (ev.repeat || String(ev.key).toLowerCase() !== tecla || !noHub()) return;',
    '          const p = pato();',
    '          if (!p || p.getVariables().get("na_loja").getAsBoolean() || p.getVariables().get("morto").getAsBoolean()) return;',
    '          N.aberto = true;',
    '          N.texto = V.get("jogador_nome").getAsString();',
    '          N.t = 0;',
    '          N.loja_antes = false;',
    '          p.getVariables().get("na_loja").setBoolean(true);',
    '          // teclas seguradas (andar) não ficam presas enquanto o painel está aberto',
    '          jogo.getInputManager().clearAllPressedKeys();',
    '        } else if (ev.key === "Enter") N.fecha(true);',
    '        else if (ev.key === "Escape") N.fecha(false);',
    '        else if (ev.key === "Backspace") N.texto = Array.from(N.texto).slice(0, -1).join("");',
    '        else if (ev.key.length === 1 && valido(ev.key) && Array.from(N.texto).length < V.get("nome_tela").getChild("max").getAsNumber()) N.texto += ev.key;',
    '        // a tecla não chega ao jogo (nem a soltura dela)',
    '        N.engolidas.add(ev.code);',
    '        ev.preventDefault();',
    '        ev.stopImmediatePropagation();',
    '      } catch (e) {}',
    '    }, true);',
    '    window.addEventListener("keyup", (ev) => {',
    '      if (N.engolidas.delete(ev.code)) { ev.preventDefault(); ev.stopImmediatePropagation(); }',
    '    }, true);',
    '    window.addEventListener("paste", (ev) => {',
    '      try {',
    '        if (!N.aberto) return;',
    '        const max = V.get("nome_tela").getChild("max").getAsNumber();',
    '        const s = Array.from((ev.clipboardData && ev.clipboardData.getData("text")) || "").filter(valido);',
    '        N.texto = Array.from(N.texto).concat(s).slice(0, max).join("");',
    '        ev.preventDefault();',
    '      } catch (e) {}',
    '    }, true);',
    '  }',
    '  // trocou de cena com o painel aberto: fecha sem salvar',
    '  if (N.aberto && N.ultimaCena && N.ultimaCena !== runtimeScene) N.aberto = false;',
    '  N.ultimaCena = runtimeScene;',
    '  N.quadro = runtimeScene.getTimeManager().getTimeFromStart();',
    '  N.t += runtimeScene.getTimeManager().getElapsedTime() / 1000;',
    '',
    '  // desenho, na camada HUD (coordenadas da tela)',
    '  const camada = runtimeScene.hasLayer("HUD") ? "HUD" : "";',
    '  const L = runtimeScene.getLayer(camada);',
    '  const x0 = L.getCameraX() - W / 2;',
    '  const y0 = L.getCameraY() - H / 2;',
    '  const st = runtimeScene.__nome || (runtimeScene.__nome = {});',
    '  const obj = (id, tipo) => {',
    '    if (!st[id]) { st[id] = runtimeScene.createObject(tipo); st[id].setLayer(camada); st[id].setZOrder(100000); }',
    '    return st[id];',
    '  };',
    '  const txt = (id, s, x, y, tam, c, alinha) => {',
    '    const o = obj(id, "nome_txt");',
    '    o.setString(limpa(s));',
    '    o.setCharacterSize(tam);',
    '    o.setColor(c);',
    '    o.hide(false);',
    '    o.setX(x0 + (alinha === "meio" ? x - o.getWidth() / 2 : x));',
    '    o.setY(y0 + y);',
    '    return o;',
    '  };',
    '  const tecla = V.get("nome_tela").getChild("tecla").getAsString().toUpperCase();',
    '  const nome = V.get("jogador_nome").getAsString();',
    '  const dica = txt("dica", tecla + "  " + (nome ? "NOME: " + nome : "ESCOLHA SEU NOME PARA O PLACAR"),',
    '    W * n("dica_x"), 0, n("tam_dica"), nome ? cor("ui_cor_rotulo") : cor("ui_cor_ouro"));',
    '  dica.setY(y0 + H * n("dica_y") - dica.getHeight());',
    '  dica.hide(N.aberto);',
    '  const painel = obj("painel", "nome_painel");',
    '  painel.clear();',
    '  for (const id of ["titulo", "nome", "ajuda"]) if (st[id]) st[id].hide(true);',
    '  if (!N.aberto) return;',
    '  const pw = n("painel_w"), ph = n("painel_h"), b = n("painel_borda");',
    '  const px = W / 2 - pw / 2, py = H / 2 - ph / 2;',
    '  painel.setFillOpacity(n("painel_opacidade"));',
    '  painel.setOutlineSize(b);',
    '  painel.setOutlineColor(cor("ui_cor_ouro"));',
    '  painel.setFillColor(cor("ui_cor_fundo"));',
    '  painel.drawRectangle(x0 + px, y0 + py, x0 + px + pw, y0 + py + ph);',
    '  const t = txt("titulo", "SEU NOME NO PLACAR", W / 2, py + n("gap"), n("tam_titulo"), cor("ui_cor_ouro"), "meio");',
    '  const cursor = Math.floor(N.t / n("pisca")) % 2 === 0 ? "_" : " ";',
    '  const max = n("max");',
    '  const nm = txt("nome", N.texto + cursor, W / 2, t.getY() - y0 + t.getHeight() + n("gap"), n("tam_nome"), cor("ui_cor_texto"), "meio");',
    '  txt("ajuda", "ENTER SALVA   ESC CANCELA   " + Array.from(N.texto).length + "/" + max, W / 2,',
    '    nm.getY() - y0 + nm.getHeight() + n("gap"), n("tam_ajuda"), cor("ui_cor_dim"), "meio");',
    '} catch (e) { /* o painel do nome nunca trava o jogo */ }',
]


def js(linhas):
    return {'type': 'BuiltinCommonInstructions::JsCode', 'inlineCode': linhas, 'parameterObjects': '', 'useStrict': True,
            'eventsSheetExpanded': False}


def migra(d):
    ids = Ids('t204')
    if not any(v['name'] == 'nome_tela' for v in d['variables']):
        d['variables'].append({'name': 'nome_tela', 'persistentUuid': ids('var/global/nome_tela'), 'type': 'structure',
                               'children': [var(ids, 'global/nome_tela', k, v) for k, v in TELA]})
    if not objeto(d, 'nome_txt'):
        o = copy.deepcopy(objeto(d, 'ui_txt'))
        o.update(name='nome_txt', persistentUuid=ids('obj/nome_txt'), variables=[], string='')
        poe_objeto(d, o, 'ui')
    if not objeto(d, 'nome_painel'):
        o = copy.deepcopy(objeto(d, 'ui_fundo_hud'))
        o.update(name='nome_painel', persistentUuid=ids('obj/nome_painel'), variables=[])
        poe_objeto(d, o, 'ui')
    folha(d, 'Hubs')['events'].append(grupo('Nome do jogador', [js(NOME)]))


if __name__ == '__main__':
    roda(migra, lambda d: any(v['name'] == 'nome_tela' for v in d['variables']), 't204')
