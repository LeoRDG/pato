"""Uma fonte só (tools/t187_fonte_unica.py): todo texto usa a Name Smile, as outras fontes saem do jogo, e o que
aparece na tela não tem acento (a Name Smile só tem ASCII; letra fora dela cairia em outra fonte)."""
import json, os, re, subprocess, unittest

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FONTE = 'Name Smile.otf'


def fontes_usadas(o, achadas):
    if isinstance(o, dict):
        if o.get('type') == 'TextObject::Text':
            achadas.add(o.get('font'))
            achadas.add(o.get('content', {}).get('font'))
        for v in o.values():
            fontes_usadas(v, achadas)
    elif isinstance(o, list):
        for v in o:
            fontes_usadas(v, achadas)
    return achadas


class FonteUnica(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.d = json.load(open(os.path.join(RAIZ, 'jogo.json'), encoding='utf-8'))

    def test_todo_texto_usa_a_name_smile(self):
        self.assertEqual(fontes_usadas(self.d, set()), {FONTE})

    def test_so_sobra_uma_fonte(self):
        fontes = [r['file'] for r in self.d['resources']['resources'] if r['kind'] in ('font', 'bitmapFont')]
        self.assertEqual(fontes, ['assets/' + FONTE])
        no_git = subprocess.run(['git', 'ls-files', 'assets'], cwd=RAIZ, capture_output=True, text=True).stdout
        arquivos = [f for f in no_git.splitlines() if re.search(r'\.(ttf|otf|woff2?|fnt)$', f, re.I)]
        self.assertEqual(arquivos, ['assets/' + FONTE])

    def test_texto_da_tela_sem_acento(self):
        from fontTools.ttLib import TTFont
        tem = TTFont(os.path.join(RAIZ, 'assets', FONTE)).getBestCmap()
        fora = set()

        def olha(s, onde):
            for ch in s:
                if ord(ch) > 127 and ord(ch) not in tem:
                    fora.add((onde, s[:60]))

        def anda(o):
            if isinstance(o, dict):
                if 'value' in o and isinstance(o.get('value'), str) and 'persistentUuid' in o:
                    olha(o['value'], 'variável')
                if isinstance(o.get('parameters'), list) and isinstance(o.get('type'), dict):
                    for p in o['parameters']:
                        olha(''.join(re.findall(r'"((?:[^"\\]|\\.)*)"', p)), 'evento')
                if o.get('type') == 'TextObject::Text':
                    olha(o.get('string', ''), 'texto')
                for v in o.values():
                    anda(v)
            elif isinstance(o, list):
                for v in o:
                    anda(v)
        for k in ('objects', 'variables', 'layouts', 'externalEvents'):   # extensões: só a fonte
            anda(self.d[k])
        self.assertEqual(fora, set())

    def test_descricao_da_loja_cabe_no_painel(self):
        import sys
        sys.path.insert(0, os.path.join(RAIZ, 'tools'))
        import gd_mig as m
        loja = json.dumps(m.folha(self.d, 'Loja')['events'], ensure_ascii=False)
        self.assertIn('"TextObject::SetWrapping"}, "parameters": ["loja_desc", "yes"]', loja)
        self.assertIn('"loja_desc", "=", "loja_largura - loja_desc_margem"', loja)
        self.assertIn('"loja_desc.Y() + loja_desc.Height() + loja_desc_margem"', loja)
        for h in ('Hub', 'HubPurgatorio', 'HubParaiso'):
            self.assertIn('loja_desc_margem', {v['name'] for v in m.cena(self.d, h)['variables']}, h)


if __name__ == '__main__':
    unittest.main()
