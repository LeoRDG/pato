"""Tarefa 221: escolher o nome do placar no celular.

O painel do nome (t204) só abria com a tecla N e só lia teclas físicas: no celular não havia como digitar. Agora,
com os controles de toque ligados (toque.ativo):
- a dica do canto vira "TOQUE AQUI PARA ESCOLHER SEU NOME" (ou "NOME: X - TOQUE PARA TROCAR"), maior
  (nome_tela.tam_dica_celular), e tocar nela (com nome_tela.toque_folga px de folga em volta) abre o painel;
- o toque foca um campo de texto invisível, o que abre o teclado do aparelho (o navegador só deixa abrir o teclado
  dentro do próprio toque, por isso é feito no touchend e não num evento do quadro); o que se digita vai para o
  painel com as mesmas regras de caracteres e de tamanho;
- o OK do teclado salva; tocar fora do painel salva e fecha; tocar no painel reabre o teclado se ele foi escondido;
- o painel fica no alto da tela (nome_tela.y_celular, fração da altura), porque o teclado cobre a metade de baixo.
No computador nada muda (N, Enter, Esc). Rodar uma vez:  python3 tools/t221_nome_no_celular.py
"""
from gd_mig import *

NOVAS = [('toque_folga', 40), ('y_celular', 0.04), ('tam_dica_celular', 40)]

TROCAS = [
    # números crus (sem escala) ganham y_celular
    ('const crus = ["max", "ref_w", "dica_x", "dica_y", "painel_opacidade", "pisca"];',
     'const crus = ["max", "ref_w", "dica_x", "dica_y", "painel_opacidade", "pisca", "y_celular"];'),
    # fechar: sai do campo de texto e não roda duas vezes (o blur do campo também fecha)
    ('''    N.fecha = (salva) => {
      try {''',
     '''    N.fecha = (salva) => {
      if (!N.aberto) return;
      N.aberto = false;
      try { if (N.campo && document.activeElement === N.campo) N.campo.blur(); } catch (e) {}
      try {'''),
    # abrir vira uma função, usada pela tecla N e pelo toque
    ('''    const noHub = () =>''',
     '''    N.abre = () => {
      const p = pato();
      if (!p || p.getVariables().get("na_loja").getAsBoolean() || p.getVariables().get("morto").getAsBoolean()) return false;
      N.aberto = true;
      N.texto = V.get("jogador_nome").getAsString();
      N.t = 0;
      N.loja_antes = false;
      p.getVariables().get("na_loja").setBoolean(true);
      // teclas seguradas (andar) não ficam presas enquanto o painel está aberto
      jogo.getInputManager().clearAllPressedKeys();
      return true;
    };
    // celular (t221): um campo de texto invisível abre o teclado do aparelho; o que se digita vai para N.texto
    N.campoAbre = () => {
      let c = N.campo;
      if (!c) {
        c = N.campo = document.createElement("input");
        c.type = "text";
        c.autocomplete = "off";
        c.autocapitalize = "characters";
        c.spellcheck = false;
        c.setAttribute("autocorrect", "off");
        c.setAttribute("enterkeyhint", "done");
        // 16px: o iPhone não dá zoom no campo
        c.style.cssText = "position:fixed;left:0;top:0;width:1px;height:1px;opacity:0;font-size:16px;border:0;padding:0;";
        c.addEventListener("input", () => {
          const max = V.get("nome_tela").getChild("max").getAsNumber();
          N.texto = Array.from(c.value).filter(valido).slice(0, max).join("");
          if (c.value !== N.texto) c.value = N.texto;
        });
        // as teclas do campo não chegam ao jogo; OK/Enter salva
        c.addEventListener("keydown", (ev) => {
          ev.stopPropagation();
          if (ev.key === "Enter") { ev.preventDefault(); N.fecha(true); }
        });
        c.addEventListener("keyup", (ev) => ev.stopPropagation());
        c.addEventListener("blur", () => { if (N.aberto) N.fecha(true); });
        document.body.appendChild(c);
      }
      c.maxLength = V.get("nome_tela").getChild("max").getAsNumber();
      c.value = N.texto;
      c.focus();
    };
    const noHub = () =>'''),
    ('''          const p = pato();
          if (!p || p.getVariables().get("na_loja").getAsBoolean() || p.getVariables().get("morto").getAsBoolean()) return;
          N.aberto = true;
          N.texto = V.get("jogador_nome").getAsString();
          N.t = 0;
          N.loja_antes = false;
          p.getVariables().get("na_loja").setBoolean(true);
          // teclas seguradas (andar) não ficam presas enquanto o painel está aberto
          jogo.getInputManager().clearAllPressedKeys();
        } else''',
     '''          if (!N.abre()) return;
        } else'''),
    # o campo de texto do celular recebe as próprias teclas (o painel não as intercepta)
    ('''        if (ev.ctrlKey || ev.metaKey || ev.altKey) return;''',
     '''        if (ev.ctrlKey || ev.metaKey || ev.altKey) return;
        if (N.campo && ev.target === N.campo) return;'''),
    # toque: na dica abre; com o painel aberto, fora dele salva e fecha, nele reabre o teclado
    ('''    window.addEventListener("keyup", (ev) => {''',
     '''    document.addEventListener("touchend", (ev) => {
      try {
        if (!V.get("toque").getChild("ativo").getAsBoolean() || !noHub()) return;
        const tq = ev.changedTouches && ev.changedTouches[0];
        if (!tq) return;
        const r = jogo.getRenderer().getCanvas().getBoundingClientRect();
        const gx = (tq.clientX - r.left) * jogo.getGameResolutionWidth() / r.width;
        const gy = (tq.clientY - r.top) * jogo.getGameResolutionHeight() / r.height;
        const dentro = (q) => q && gx >= q.x0 && gx <= q.x1 && gy >= q.y0 && gy <= q.y1;
        if (!N.aberto) {
          if (dentro(N.dicaRet) && N.abre()) N.campoAbre();
        } else if (dentro(N.painelRet)) N.campoAbre();
        else N.fecha(true);
      } catch (e) {}
    }, true);
    window.addEventListener("keyup", (ev) => {'''),
    # dica: no celular é para tocar; guarda o retângulo dela (coordenadas da tela do jogo) para o toque
    ('''  const dica = txt("dica", tecla + "  " + (nome ? "NOME: " + nome : "ESCOLHA SEU NOME PARA O PLACAR"),
    W * n("dica_x"), 0, n("tam_dica"), nome ? cor("ui_cor_rotulo") : cor("ui_cor_ouro"));
  dica.setY(y0 + H * n("dica_y") - dica.getHeight());''',
     '''  const toque = V.get("toque").getChild("ativo").getAsBoolean();
  const textoDica = toque ? (nome ? "NOME: " + nome + " - TOQUE PARA TROCAR" : "TOQUE AQUI PARA ESCOLHER SEU NOME")
    : tecla + "  " + (nome ? "NOME: " + nome : "ESCOLHA SEU NOME PARA O PLACAR");
  const dica = txt("dica", textoDica, W * n("dica_x"), 0, n(toque ? "tam_dica_celular" : "tam_dica"),
    nome ? cor("ui_cor_rotulo") : cor("ui_cor_ouro"));
  dica.setY(y0 + H * n("dica_y") - dica.getHeight());
  const folga = n("toque_folga");
  N.dicaRet = { x0: dica.getX() - x0 - folga, x1: dica.getX() - x0 + dica.getWidth() + folga,
    y0: dica.getY() - y0 - folga, y1: dica.getY() - y0 + dica.getHeight() + folga };'''),
    # painel: no celular fica no alto (o teclado cobre a metade de baixo); guarda o retângulo para o toque
    ('''  const px = W / 2 - pw / 2, py = H / 2 - ph / 2;''',
     '''  const px = W / 2 - pw / 2, py = toque ? H * n("y_celular") : H / 2 - ph / 2;
  N.painelRet = { x0: px, x1: px + pw, y0: py, y1: py + ph };'''),
    ('''  txt("ajuda", "ENTER SALVA   ESC CANCELA   " + Array.from(N.texto).length + "/" + max, W / 2,''',
     '''  txt("ajuda", (toque ? "OK SALVA   TOQUE FORA PARA SAIR   " : "ENTER SALVA   ESC CANCELA   ") + Array.from(N.texto).length + "/" + max, W / 2,'''),
]


def migra(d):
    h = folha(d, 'Hubs')
    g = acha(h['events'], 'Nome do jogador')
    js = next(e for e in g['events'] if e['type'] == 'BuiltinCommonInstructions::JsCode')
    codigo = '\n'.join(js['inlineCode'])
    assert 'Nome do jogador (t204)' in codigo
    for velho, novo in TROCAS:
        assert codigo.count(velho) == 1, velho[:80]
        codigo = codigo.replace(velho, novo)
    codigo = codigo.replace('// Nome do jogador (t204): N abre o painel no hub, Enter salva, Esc cancela.',
                            '// Nome do jogador (t204): N abre o painel no hub, Enter salva, Esc cancela. No celular (t221),'
                            ' tocar na dica abre o teclado do aparelho.')
    js['inlineCode'] = codigo.split('\n')
    t = next(v for v in d['variables'] if v['name'] == 'nome_tela')
    poe_vars(Ids('t221'), t['children'], 'global/nome_tela', NOVAS)


if __name__ == '__main__':
    roda(migra, lambda d: any(c['name'] == 'y_celular' for v in d['variables'] if v['name'] == 'nome_tela'
                              for c in v['children']), 't221')
