"""Tarefa 33: correções da revisão da loja (só mexe nos eventos criados pelas tarefas 31 e 32).

1. Clique só compra sobre uma linha e só depois de uma pressão NOVA do botão com a loja aberta
   (segurar o tiro, abrir a loja e soltar não gasta moedas). Espaço e clique viram loja_comprar = 1.
2. 'requer' aceita id de upgrade ou de arma.
3. O rastro da barra do mercador encolhe até a vida (velocidade em trader.rastro_vel).
Rodar uma vez:  python3 tools/t33_loja_revisao.py   (feche o projeto no GDevelop antes)
"""
import json
from migra import carrega, salva, var, adiciona_var, objeto, cena, externo, anda, C, A, E, comentario

REQ_VELHO = 'GlobalVariable(upgrades[loja_req])'
REQ_NOVO = 'max(GlobalVariable(upgrades[loja_req]), GlobalVariable(armas[loja_req]))'


def unico(lista, desc):
    if len(lista) != 1:
        raise SystemExit(f'{desc}: esperado 1, achei {len(lista)}; nada alterado')
    return lista[0]


def main():
    d = carrega()
    loja = externo(d, 'Loja')['events']
    g = {e.get('name'): e for e in loja}
    if 'loja_comprar' in json.dumps(g['Compra']):
        print('já migrado'); return

    # 1. compra
    compra = g['Compra']['events']
    principal = unico([e for e in compra if any(a['parameters'][:2] == ['moedas_total', '-'] for a in e.get('actions') or [])], 'compra')
    ou = unico([c for c in principal['conditions'] if c['type']['value'] == 'BuiltinCommonInstructions::Or'], 'Or da compra')
    principal['conditions'][principal['conditions'].index(ou)] = C('NumberVariable', 'loja_comprar', '=', '1')
    aberta = C('BooleanVariable', 'loja_aberta', 'True', '')
    sobre = C('SourisSurObjet', 'loja_linha', '', 'yes')
    lmb = C('MouseButtonFromTextPressed', '', '"Left"')
    gatilhos = [
        E([], [A('SetNumberVariable', 'loja_comprar', '=', '0')]),
        E([aberta, C('KeyFromTextJustPressed', '', '"Space"')], [A('SetNumberVariable', 'loja_comprar', '=', '1')]),
        E([aberta, lmb, C('BooleanVariable', 'loja_lmb_antes', 'False', ''), sobre],
          [A('SetBooleanVariable', 'loja_lmb_ok', 'True', '')]),
        E([aberta, C('MouseButtonFromTextReleased', '', '"Left"'), C('BooleanVariable', 'loja_lmb_ok', 'True', ''), sobre],
          [A('SetNumberVariable', 'loja_comprar', '=', '1')]),
        E([lmb], [A('SetBooleanVariable', 'loja_lmb_antes', 'True', '')]),
        E([C('MouseButtonFromTextPressed', '', '"Left"', inv=True)],
          [A('SetBooleanVariable', 'loja_lmb_antes', 'False', ''), A('SetBooleanVariable', 'loja_lmb_ok', 'False', '')]),
    ]
    i = compra.index(principal)
    compra[i:i] = [comentario('Clique só vale se o botão foi apertado de novo sobre uma linha com a loja aberta, e solto sobre uma linha.')] + gatilhos

    # 2. requer
    req = [c for e in anda([g['Menu']]) for c in e.get('conditions') or [] if c['parameters'][:1] == [REQ_VELHO]]
    unico(req, 'condição do requer')['parameters'][0] = REQ_NOVO

    # 3. rastro da barra
    adiciona_var(objeto(d, 'trader')['variables'], var('rastro_vel', 300))
    barra = unico([e for e in g['Barra do mercador']['events'] if e.get('conditions')], 'evento da barra')
    barra['events'] += [
        E([C('BuiltinCommonInstructions::CompareNumbers', 'hud_boss_rastro.Width()', '>', 'hud_boss_fill.Width()')],
          [A('ResizableCapability::ResizableBehavior::SetWidth', 'hud_boss_rastro', 'Resizable', '-', 'trader.rastro_vel * TimeDelta()')]),
        E([C('BuiltinCommonInstructions::CompareNumbers', 'hud_boss_rastro.Width()', '<', 'hud_boss_fill.Width()')],
          [A('ResizableCapability::ResizableBehavior::SetWidth', 'hud_boss_rastro', 'Resizable', '=', 'hud_boss_fill.Width()')]),
    ]

    hub = cena(d, 'Hub')
    for k, v in dict(loja_comprar=0, loja_lmb_antes=False, loja_lmb_ok=False).items():
        adiciona_var(hub['variables'], var(k, v))
    salva(d)
    print('ok')


if __name__ == '__main__':
    main()
