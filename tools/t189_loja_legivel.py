"""Tarefa 189: loja mais fácil de ler.
- A descrição (loja_desc) ganha entrelinha (lineHeight 32 para a fonte 24): com a Name Smile as linhas encostavam.
- O painel fica quase opaco (fillOpacity 190 -> 240): o mercador e o pato apareciam atrás do texto.
- A linha escolhida ganha uma faixa atrás (objeto loja_faixa, um Drawer na camada HUD entre o painel e o texto),
  da largura do painel e da altura de uma linha (loja_linha_alt). Antes só a cor marcava a escolha, e o amarelo
  dela era quase o mesmo do MAX. Cor e opacidade da faixa ficam no objeto.
Rodar uma vez:  python3 tools/t189_loja_legivel.py
"""
import copy
from gd_mig import *


def migra(d):
    ids = Ids('t189')
    desc = objeto(d, 'loja_desc')['content']
    if not desc['lineHeight']:
        desc['lineHeight'] = 32
    painel = objeto(d, 'loja_painel')
    if painel['fillOpacity'] == 190:
        painel['fillOpacity'] = 240
    faixa = copy.deepcopy(painel)
    faixa.update(name='loja_faixa', persistentUuid=ids('obj/loja_faixa'), fillOpacity=45,
                 fillColor={'r': 255, 'g': 230, 'b': 120})
    poe_objeto(d, faixa, 'hub')

    for e in todos(folha(d, 'Loja')['events']):
        acs = e.get('actions', [])
        txt = json.dumps(acs)
        if '"Create"}, "parameters": ["", "loja_painel"' in txt:
            i = next(k for k, a in enumerate(acs) if a['parameters'][:1] == ['loja_painel']
                     and a['type']['value'] == 'ChangePlan') + 1
            acs[i:i] = [X('Create', '', 'loja_faixa', '0', '0', '"HUD"'),
                        X('ChangePlan', 'loja_faixa', '=', 'loja_painel.ZOrder() + 1')]
        elif '"Delete"}, "parameters": ["loja_painel"' in txt:
            acs.insert(1, X('Delete', 'loja_faixa', ''))
    ret = next(a for e in todos(folha(d, 'Loja')['events']) for a in e.get('actions', [])
               if a['type']['value'] == 'PrimitiveDrawing::Rectangle' and a['parameters'][0] == 'loja_painel')
    for e in todos(folha(d, 'Loja')['events']):
        if '"loja_linha", "indice", "=", "loja_sel"' in json.dumps(e.get('conditions', [])):
            meio = 'loja_linha.Y() + loja_linha.Height() / 2'
            e['actions'].insert(0, X('PrimitiveDrawing::Rectangle', 'loja_faixa', ret['parameters'][1],
                                     f'{meio} - loja_linha_alt / 2', ret['parameters'][3],
                                     f'{meio} + loja_linha_alt / 2'))


if __name__ == '__main__':
    roda(migra, lambda d: objeto(d, 'loja_faixa') is not None, 't189')
