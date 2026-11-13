"""Tarefa 35: boneco de teste das armas no Hub (só adiciona o que falta).

- Objeto 'boneco': cópia do 'condenado' (todas as variáveis de inimigo e gravidade) com o visual da 'estatua'.
  Só entra nos grupos Inimigo e Personagem: leva bala, explosão e soco, mostra números de dano e barra de vida,
  mas não tem IA. estado "calmo" = não machuca ao encostar; dano 0 e qtd_moedas 0.
- Vida cheia (boneco.vida / max_vida) e, depois de boneco.regen_espera segundos sem levar dano, volta à vida cheia.
- Uma instância no Hub, à direita do mercador.
Rodar uma vez:  python3 tools/t35_boneco.py   (feche o projeto no GDevelop antes)
"""
import copy, uuid
from migra import carrega, salva, var, adiciona_var, acha_var, objeto, cena, copia_objeto, C, A, E, comentario, grupo

VALORES = dict(vida=1000, max_vida=1000, dano=0, qtd_moedas=0, estado='calmo', sangue='lasca')
X, Y, LARG, ALT = 1700, 560, 144, 240


def main():
    d = carrega()
    if objeto(d, 'boneco'):
        print('boneco já existe; nada feito'); return
    b = copia_objeto(d, 'condenado', 'boneco')
    b['animations'] = copy.deepcopy(objeto(d, 'estatua')['animations'])
    for k, val in VALORES.items():
        acha_var(b['variables'], k)['value'] = val
    adiciona_var(b['variables'], var('regen_espera', 1.5))
    adiciona_var(b['variables'], var('vida_vista', 0))
    for g in d['objectsGroups']:
        if g['name'] in ('Inimigo', 'Personagem'):
            g['objects'].append({'name': 'boneco'})

    hub = cena(d, 'Hub')
    hub['instances'].append({'angle': 0, 'customSize': True, 'depth': 1, 'height': ALT, 'keepRatio': True, 'layer': '',
                             'name': 'boneco', 'persistentUuid': str(uuid.uuid4()), 'width': LARG, 'x': X, 'y': Y,
                             'zOrder': 1002, 'numberProperties': [], 'stringProperties': [], 'initialVariables': []})
    eventos = grupo('Boneco de teste', [
        comentario('Boneco para testar as armas: leva dano de tudo e, depois de boneco.regen_espera s sem dano, volta à vida cheia.'),
        E([C('SceneJustBegins', '')], [A('SetNumberObjectVariable', 'boneco', 'vida_vista', '=', 'boneco.vida')]),
        E([C('NumberObjectVariable', 'boneco', 'vida', '<', 'boneco.vida_vista')],
          [A('ResetObjectTimer', 'boneco', '"sem_dano"'),
           A('SetNumberObjectVariable', 'boneco', 'vida_vista', '=', 'boneco.vida')]),
        E([C('NumberObjectVariable', 'boneco', 'vida', '<', 'boneco.max_vida'),
           C('CompareObjectTimer', 'boneco', '"sem_dano"', '>', 'boneco.regen_espera')],
          [A('SetNumberObjectVariable', 'boneco', 'vida', '=', 'boneco.max_vida'),
           A('SetNumberObjectVariable', 'boneco', 'vida_vista', '=', 'boneco.max_vida')]),
    ])
    links = [i for i, e in enumerate(hub['events']) if e['type'] == 'BuiltinCommonInstructions::Link' and e.get('target') == 'Loja']
    hub['events'].insert(links[-1] if links else len(hub['events']), eventos)
    salva(d)
    print('ok')


if __name__ == '__main__':
    main()
