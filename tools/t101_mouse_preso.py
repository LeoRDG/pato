"""Tarefa 101: o mouse não sai do jogo.

Nas cenas com os eventos do Jogador (Hub, Inferno, Purgatório, Paraíso), o primeiro clique trava o ponteiro no jogo
(pointer lock do navegador / Electron). Com ele travado, o movimento do mouse anda um cursor virtual que fica preso
dentro da tela do jogo, e esse cursor é o que MouseX()/MouseY() leem: a mira e os cliques (loja) continuam iguais.
A sensibilidade é a variável global nova mouse_sensibilidade (1). Esc solta o ponteiro (o navegador obriga) e o
próximo clique trava de novo. Saindo para uma cena sem o Jogador (Menu, Vitória), o ponteiro é solto.
Rodar uma vez:  python3 tools/t101_mouse_preso.py
"""
import json, os, sys, uuid

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

JS = r"""// Mouse preso no jogo: pointer lock + cursor virtual dentro da tela (é o que MouseX()/MouseY() leem).
// Roda todo quadro só nas cenas com o Jogador; a sensibilidade é a variável global mouse_sensibilidade.
const jogo = runtimeScene.getGame();
const T = gdjs._mousePreso || (gdjs._mousePreso = {});
T.jogo = jogo;
T.cena = runtimeScene;
if (!T.instalado) {
  T.instalado = true;
  const canvas = jogo.getRenderer().getCanvas();
  const im = () => T.jogo.getInputManager();
  const travado = () => document.pointerLockElement === canvas;
  const ativo = () => T.jogo.getSceneStack().getCurrentScene() === T.cena;
  const sens = () => {
    const v = T.jogo.getVariables();
    return v.has("mouse_sensibilidade") ? v.get("mouse_sensibilidade").getAsNumber() : 1;
  };
  const aplica = () => { if (travado()) im().onMouseMove(T.x, T.y); };
  canvas.addEventListener("mousedown", () => {
    if (ativo() && !travado()) {
      T.x = im().getCursorX();
      T.y = im().getCursorY();
      canvas.requestPointerLock();
    }
  });
  // na janela (depois do canvas): o jogo já leu a posição congelada do ponteiro; o cursor virtual passa por cima
  window.addEventListener("mousemove", (e) => {
    if (!travado()) return;
    const r = canvas.getBoundingClientRect();
    const w = T.jogo.getGameResolutionWidth(), h = T.jogo.getGameResolutionHeight();
    T.x = Math.min(w, Math.max(0, T.x + e.movementX * sens() * w / r.width));
    T.y = Math.min(h, Math.max(0, T.y + e.movementY * sens() * h / r.height));
    aplica();
  });
  window.addEventListener("mousedown", aplica);
  window.addEventListener("mouseup", aplica);
  const quadro = () => {
    if (travado() && !ativo()) document.exitPointerLock();
    aplica();
    requestAnimationFrame(quadro);
  };
  requestAnimationFrame(quadro);
}
"""


def main(caminho):
    texto = open(caminho, encoding='utf-8').read()
    d = json.loads(texto)
    if 'gdjs._mousePreso' in texto:
        sys.exit('t101 já foi aplicada; não roda de novo.')
    j = next(x for x in d['externalEvents'] if x['name'] == 'Jogador')['events']
    j.insert(0, {
        'type': 'BuiltinCommonInstructions::Group', 'name': 'Mouse preso', 'source': '', 'creationTime': 0,
        'events': [
            {'type': 'BuiltinCommonInstructions::Comment',
             'color': {'b': 109, 'g': 230, 'r': 255, 'textB': 0, 'textG': 0, 'textR': 0},
             'comment': 'O primeiro clique trava o ponteiro no jogo; o mouse anda um cursor virtual preso na tela '
                        '(MouseX()/MouseY()). Sensibilidade: variável global mouse_sensibilidade. Esc solta; '
                        'clicar trava de novo. Em cena sem o Jogador o ponteiro é solto.'},
            {'type': 'BuiltinCommonInstructions::JsCode', 'inlineCode': JS.strip('\n').split('\n'),
             'parameterObjects': '', 'useStrict': True, 'eventsSheetExpanded': False}]})
    if not any(v['name'] == 'mouse_sensibilidade' for v in d['variables']):
        d['variables'].append({'name': 'mouse_sensibilidade',
                               'persistentUuid': str(uuid.uuid5(uuid.NAMESPACE_URL, 'jogos/t101/mouse_sensibilidade')),
                               'type': 'number', 'value': 1})

    novo = json.dumps(d, indent=2, ensure_ascii=False) + '\n'
    if '0.000001' in texto:
        novo = novo.replace('"value": 1e-06', '"value": 0.000001')
    with open(caminho, 'w', encoding='utf-8') as f:
        f.write(novo)
    print('mouse preso no jogo')


if __name__ == '__main__':
    main(sys.argv[1] if len(sys.argv) > 1 else os.path.join(RAIZ, 'jogo.json'))
