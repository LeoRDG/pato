"""Tarefa 187: a Name Smile é a fonte do jogo.
- Todo TextObject (objetos globais, de cena e os modelos das extensões) passa a usar 'Name Smile.otf'.
- As outras fontes (CantoraOne, NotoSansArabicUI) saem dos recursos (os arquivos são apagados no mesmo commit).
- A Name Smile só tem ASCII: o texto que aparece na tela perde os acentos (DEMONIO, GUARDIAO, MAX, LANCA-GRANADAS,
  as descrições da loja, as placas da sala de teste). Extensões e nomes de grupos/eventos e comentários ficam como estão.
  O "·" da dica das armas vira "-".
- A Name Smile é mais larga: a descrição da loja quebra linha dentro do painel (loja_largura - loja_desc_margem) e o
  painel cresce até o fim da descrição (antes a altura supunha uma linha só).
Rodar uma vez:  python3 tools/t187_fonte_unica.py
"""
import re, unicodedata
from gd_mig import *

FONTE = 'Name Smile.otf'


def sem_acento(s):
    s = s.replace('·', '-')
    return ''.join(c for c in unicodedata.normalize('NFKD', s) if not unicodedata.combining(c))


def anda(o, textos=True):
    if isinstance(o, dict):
        if o.get('type') == 'TextObject::Text':
            o['font'] = FONTE
            if isinstance(o.get('content'), dict):
                o['content']['font'] = FONTE
        if not textos:
            for v in o.values():
                anda(v, False)
            return
        # valor de variável (de objeto, global, de instância): texto mostrado
        if 'persistentUuid' in o and o.get('type') == 'string' and isinstance(o.get('value'), str):
            o['value'] = sem_acento(o['value'])
        # parâmetros de condições/ações: só os textos entre aspas
        if isinstance(o.get('parameters'), list) and isinstance(o.get('type'), dict):
            o['parameters'] = [re.sub(r'"((?:[^"\\]|\\.)*)"', lambda m: '"' + sem_acento(m.group(1)) + '"', p)
                               for p in o['parameters']]
        if o.get('type') == 'TextObject::Text' and isinstance(o.get('string'), str):
            o['string'] = sem_acento(o['string'])
            if isinstance(o.get('content'), dict) and isinstance(o['content'].get('text'), str):
                o['content']['text'] = sem_acento(o['content']['text'])
        for k, v in o.items():
            if k not in ('inlineCode',):
                anda(v)
    elif isinstance(o, list):
        for v in o:
            anda(v, textos)


def loja(d):
    for h in ('Hub', 'HubPurgatorio', 'HubParaiso'):
        poe_vars(Ids('t187'), cena(d, h)['variables'], h, [('loja_desc_margem', 24)])
    for e in todos(folha(d, 'Loja')['events']):
        acs = e.get('actions', [])
        tipos = [a['type']['value'] for a in acs]
        if 'Create' in tipos and acs[tipos.index('Create')]['parameters'][1] == 'loja_desc' \
                and 'TextObject::SetWrapping' not in tipos:
            i = tipos.index('Create') + 1
            acs[i:i] = [X('TextObject::SetWrapping', 'loja_desc', 'yes'),
                        X('TextObject::WrappingWidth', 'loja_desc', '=', 'loja_largura - loja_desc_margem')]
        if 'PrimitiveDrawing::Rectangle' in tipos and any(
                a['parameters'][:1] == ['loja_desc'] and 'descricao' in json.dumps(a) for a in acs):
            ret = acs[tipos.index('PrimitiveDrawing::Rectangle')]
            if 'loja_desc.Height()' not in ret['parameters'][4]:
                ret['parameters'][4] = 'loja_desc.Y() + loja_desc.Height() + loja_desc_margem'
                # o texto muda antes de desenhar o painel, para a altura já ser a do texto novo
                texto = next(a for a in acs if a['parameters'][:1] == ['loja_desc'])
                acs.remove(texto)
                acs.insert(acs.index(ret), texto)


def migra(d):
    anda(d['objects'])
    anda(d['variables'])
    anda(d['layouts'])
    anda(d['externalEvents'])
    anda(d['eventsFunctionsExtensions'], textos=False)   # extensões: só a fonte
    loja(d)
    d['resources']['resources'] = [r for r in d['resources']['resources']
                                   if r['kind'] not in ('font', 'bitmapFont') or r['name'] == FONTE]


if __name__ == '__main__':
    roda(migra, lambda d: not any(r['kind'] == 'font' and r['name'] != FONTE for r in d['resources']['resources']),
         't187')
