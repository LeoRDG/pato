"""Tarefa 115: as partículas dos portais deixam de ser aditivas (deixavam o Purgatório todo claro).

Com um portal no Purgatório, o tilemap aparecia desbotado (paredes claras com borda branca) e as partículas brancas.
Testado no jogo: apagando os emissores do portal o cenário volta ao normal, e com os emissores sem renderização
aditiva também. O tilemap herda o modo de mistura aditivo deixado pelas partículas e é somado ao fundo. Os três
emissores dos portais (portal_espiral, portal_braco, portal_nucleo) passam a additive = False (propriedade
"aditivo" de cada emissor no editor).
Rodar uma vez:  python3 tools/t115_portal_sem_aditivo.py
"""
import json, os, sys

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EMISSORES = ('portal_espiral', 'portal_braco', 'portal_nucleo')


def main(caminho):
    texto = open(caminho, encoding='utf-8').read()
    d = json.loads(texto)
    mudou = [o['name'] for o in d['objects'] if o['name'] in EMISSORES and o.get('additive')]
    if not mudou:
        sys.exit('t115 já foi aplicada; não roda de novo.')
    for o in d['objects']:
        if o['name'] in mudou:
            o['additive'] = False

    novo = json.dumps(d, indent=2, ensure_ascii=False) + '\n'
    if '0.000001' in texto:
        novo = novo.replace('"value": 1e-06', '"value": 0.000001')
    with open(caminho, 'w', encoding='utf-8') as f:
        f.write(novo)
    print('sem aditivo:', mudou)


if __name__ == '__main__':
    main(sys.argv[1] if len(sys.argv) > 1 else os.path.join(RAIZ, 'jogo.json'))
