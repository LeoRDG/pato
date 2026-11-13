"""Tarefa 30: os controles do pato travam enquanto a loja está aberta (pato.na_loja).

Todo evento de 'Jogador' com condição de tecla/botão (não invertida) ganha a condição pato.na_loja = falso,
assim o clique/Espaço que compra na loja não atira, não soca e não pula. Condições invertidas ('botão solto')
continuam rodando (zeram estados), e AnyKeyReleased (resumo da morte) fica de fora.
Rodar uma vez:  python3 tools/t30_trava_controles.py   (feche o projeto no GDevelop antes)
"""
from migra import carrega, salva, externo, anda, C


def entrada(c):
    t = c['type']
    return (any(k in t['value'] for k in ('Key', 'MouseButton', 'Gamepad')) and t['value'] != 'AnyKeyReleased'
            and not t.get('inverted'))


def tem_trava(e):
    return any(c['type']['value'] == 'BooleanObjectVariable' and c['parameters'][:3] == ['pato', 'na_loja', 'False']
               for c in e['conditions'])


def main():
    d = carrega()
    n = 0
    for e in anda(externo(d, 'Jogador')['events']):
        if any(entrada(c) for c in e.get('conditions') or []) and not tem_trava(e):
            e['conditions'].append(C('BooleanObjectVariable', 'pato', 'na_loja', 'False', ''))
            n += 1
    salva(d)
    print('eventos travados:', n)


if __name__ == '__main__':
    main()
