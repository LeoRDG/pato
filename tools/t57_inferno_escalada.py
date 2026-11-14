"""Tarefa 57: trecho de plataformas móveis no alto do Inferno, do piso onde o pato está até o topo, à direita.

O pato começa no piso escuro (y = -6249, x >= 2804). Seis plataforma_movel rápidas, com vãos de uns 240 px, fazem
um zigue-zague que sobe e termina no alto, à direita, na ponta de cima da diagonal de tiles (x 5748, y -7721):

    1 sobe-desce  ->  2 vai-e-vem  ->  3 sobe-desce  ->  4 vai-e-vem  ->  5 sobe-desce  ->  6 vai-e-vem comprido
    (ao lado do pato)                  (lado direito)     (volta para a esquerda)          (no topo, acaba na direita)

Migração de uso único que só ADICIONA as seis instâncias na cena Inferno (se ainda não estão lá; cada uma tem um
persistentUuid fixo). Começo, fim, velocidade e espera ficam nas variáveis de cada instância, como nas plataformas
que já existem, e o tamanho copia o delas. Depois de criadas, mexer nelas no editor é com você: o script não volta
nenhum valor.
"""
import copy, json, os, sys, uuid

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CENA = 'Inferno'
#        nome            começo (x, y)     fim (x, y)       velocidade  espera
TRECHO = [('sobe_1', (3350, -6430), (3350, -6750), 320, 0.25),
          ('vai_2',  (4000, -6880), (4700, -6880), 420, 0.2),
          ('sobe_3', (5350, -6930), (5350, -7230), 340, 0.25),
          ('vai_4',  (4700, -7340), (3800, -7340), 450, 0.2),
          ('sobe_5', (3150, -7300), (3150, -7600), 340, 0.25),
          ('vai_6',  (3800, -7733), (5300, -7733), 480, 0.3)]
LARGURA, ALTURA = 407, 175          # usados só se a cena não tiver nenhuma plataforma_movel para copiar o tamanho


def uid(nome):
    return str(uuid.uuid5(uuid.NAMESPACE_URL, 'jogos/t57/' + nome))


def migra(d):
    cena = next(l for l in d['layouts'] if l['name'] == CENA)
    ja = {i.get('persistentUuid') for i in cena['instances']}
    molde = next((i for i in cena['instances'] if i['name'] == 'plataforma_movel'), None)
    z = max((i['zOrder'] for i in cena['instances'] if i['layer'] == '' and i['name'].startswith(('tiles_', 'plataforma_movel'))), default=0) + 1
    for nome, ini, fim, vel, espera in TRECHO:
        if uid(nome) in ja:
            continue
        if molde is not None:
            inst = copy.deepcopy(molde)
        else:
            inst = {'angle': 0, 'customSize': True, 'height': ALTURA, 'layer': '', 'name': 'plataforma_movel', 'width': LARGURA,
                    'x': 0, 'y': 0, 'zOrder': z, 'numberProperties': [], 'stringProperties': [], 'initialVariables': []}
        inst.update(x=ini[0], y=ini[1], zOrder=z, persistentUuid=uid(nome))
        inst['initialVariables'] = [{'name': k, 'persistentUuid': uid(nome + '/' + k), 'type': 'number', 'value': v} for k, v in
                                    (('ini_x', ini[0]), ('ini_y', ini[1]), ('fim_x', fim[0]), ('fim_y', fim[1]),
                                     ('velocidade', vel), ('espera', espera))]
        cena['instances'].append(inst)


def main(caminho):
    txt = open(caminho, encoding='utf-8').read()
    d = json.loads(txt)
    migra(d)
    novo = json.dumps(d, indent=2, ensure_ascii=False) + '\n'
    if '0.000001' in txt:                       # o json do Python escreveria 1e-06; mantém como o GDevelop grava
        novo = novo.replace('"value": 1e-06', '"value": 0.000001')
    with open(caminho, 'w', encoding='utf-8') as f:
        f.write(novo)


if __name__ == '__main__':
    main(sys.argv[1] if len(sys.argv) > 1 else os.path.join(RAIZ, 'jogo.json'))
