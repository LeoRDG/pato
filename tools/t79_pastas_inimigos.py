"""Tarefa 79: arruma as pastas dos inimigos por área, nas imagens e no painel de objetos do GDevelop.

Imagens: assets/gandalf_hell/<inimigo>/ (Inferno), as soltas em assets/ (zumbi, pigman, atirador, sapo, cutulu, voador:
Purgatório) e assets/anjos/<anjo>/ (Céu) vão para assets/inimigos/<area>/<inimigo>/. O caminho (`file`) de cada
recurso muda; os recursos que tinham o próprio caminho como nome (padrão do GDevelop) passam a ter o caminho
novo como nome, trocado em toda referência exata. Projéteis ficam em assets/inimigos/projeteis.
Painel de objetos: a pasta inimigos passa a ter inferno, purgatorio, ceu, projeteis e chefe (somem novos_sem_ia e
anjos_sem_ia). Só move; não mexe em valor nenhum.
Rodar uma vez:  python3 tools/t79_pastas_inimigos.py
"""
import json, os, subprocess, sys

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
AREAS = {
    'inferno': ['condenado', 'condenada', 'condenado_torto', 'condenado_azul', 'condenado_inchado', 'arvore_condenada',
                'caveira_gigante', 'caveira_azul', 'cabeca_voadora', 'diabinho', 'moscas', 'olho_demoniaco', 'mina_demoniaca'],
    'purgatorio': ['zumbi', 'pigman', 'atirador', 'sapo', 'cutulu', 'voador'],
    'ceu': ['querubim', 'serafim', 'ofanim', 'roda_anjo'],
}
PASTA_ANTIGA = {'inferno': 'assets/gandalf_hell', 'ceu': 'assets/anjos'}   # purgatório: arquivos soltos em assets/
EXTRAS_PROJETEIS = ['olho_raio']


def move(de, para):
    os.makedirs(os.path.dirname(os.path.join(RAIZ, para)), exist_ok=True)
    rastreado = subprocess.run(['git', 'ls-files', '--error-unmatch', de], cwd=RAIZ, capture_output=True).returncode == 0
    if rastreado:
        subprocess.run(['git', 'mv', de, para], cwd=RAIZ, check=True)
    else:
        os.rename(os.path.join(RAIZ, de), os.path.join(RAIZ, para))


def imagens_do_objeto(o, rec):
    fs = set()
    for a in o.get('animations', []):
        for d in a['directions']:
            for s in d['sprites']:
                fs.add(rec[s['image']]['file'])
    return fs


def main(caminho):
    txt = open(caminho, encoding='utf-8').read()
    d = json.loads(txt)
    ini = next(c for c in d['objectsFolderStructure']['children'] if c.get('folderName') == 'inimigos')
    if any(c.get('folderName') == 'purgatorio' for c in ini['children']):
        sys.exit('t79 já foi aplicada (pasta inimigos/purgatorio existe); não roda de novo.')
    rec = {r['name']: r for r in d['resources']['resources']}
    obj = {o['name']: o for o in d['objects']}

    # 1. imagens: mapa caminho antigo -> novo (pastas inteiras para Inferno/Céu, arquivo a arquivo para o Purgatório)
    novo = {}
    for area, nomes in AREAS.items():
        for n in nomes:
            destino = f'assets/inimigos/{area}/{n}'
            if area in PASTA_ANTIGA:
                origem = f'{PASTA_ANTIGA[area]}/{n}'
                if os.path.isdir(os.path.join(RAIZ, origem)):
                    move(origem, destino)
                    novo[origem + '/'] = destino + '/'
            else:
                for f in sorted(imagens_do_objeto(obj[n], rec)):
                    if os.path.dirname(f) == 'assets' and os.path.exists(os.path.join(RAIZ, f)):
                        alvo = f'{destino}/{os.path.basename(f)}'
                        move(f, alvo)
                        novo[f] = alvo
    renomeia = {}
    for r in d['resources']['resources']:
        f = r.get('file', '')
        antigo = f
        if f in novo:
            r['file'] = novo[f]
        else:
            for de, para in novo.items():
                if de.endswith('/') and f.startswith(de):
                    r['file'] = para + f[len(de):]
                    break
        if r['file'] != antigo and r['name'] == antigo:            # recurso com o nome do caminho (padrão do GDevelop)
            renomeia[antigo] = r['file']
            r['name'] = r['file']

    def troca(x):                                               # toda referência exata ao nome antigo
        if isinstance(x, dict):
            return {k: troca(v) for k, v in x.items()}
        if isinstance(x, list):
            return [troca(v) for v in x]
        return renomeia.get(x, x) if isinstance(x, str) else x
    d = troca(d)
    ini = next(c for c in d['objectsFolderStructure']['children'] if c.get('folderName') == 'inimigos')
    for velha in PASTA_ANTIGA.values():                        # assets/anjos fica vazia
        p = os.path.join(RAIZ, velha)
        if os.path.isdir(p) and not os.listdir(p):
            os.rmdir(p)

    # 2. painel de objetos
    soltos, pastas = {}, {}
    for c in ini['children']:
        if 'folderName' in c:
            pastas[c['folderName']] = c
        else:
            soltos[c['objectName']] = c

    def tira(nome):
        if nome in soltos:
            return soltos.pop(nome)
        for p in pastas.values():
            for i, c in enumerate(p.get('children', [])):
                if c.get('objectName') == nome:
                    return p['children'].pop(i)
        for p in d['objectsFolderStructure']['children']:      # objeto novo deixado na raiz
            if p.get('objectName') == nome:
                d['objectsFolderStructure']['children'].remove(p)
                return p
        return {'objectName': nome}

    filhos = []
    for area, nomes in AREAS.items():
        filhos.append({'folderName': area, 'children': [tira(n) for n in nomes if n in obj]})
    proj = pastas.pop('projeteis', {'folderName': 'projeteis', 'children': []})
    proj['children'] += [tira(n) for n in EXTRAS_PROJETEIS if n in obj and n not in json.dumps(proj)]
    filhos.append(proj)
    if 'chefe' in pastas:
        filhos.append(pastas.pop('chefe'))
    for nome, p in pastas.items():                              # o que sobrar nas pastas antigas não se perde
        if nome in ('novos_sem_ia', 'anjos_sem_ia'):
            filhos.extend(p.get('children', []))
        else:
            filhos.append(p)
    filhos.extend(soltos.values())
    ini['children'] = filhos

    saida = json.dumps(d, indent=2, ensure_ascii=False) + '\n'
    if '0.000001' in txt:
        saida = saida.replace('"value": 1e-06', '"value": 0.000001')
    with open(caminho, 'w', encoding='utf-8') as f:
        f.write(saida)
    print(f'{len(novo)} caminhos movidos; pasta inimigos: {[c.get("folderName", c.get("objectName")) for c in filhos]}')


if __name__ == '__main__':
    main(sys.argv[1] if len(sys.argv) > 1 else os.path.join(RAIZ, 'jogo.json'))
