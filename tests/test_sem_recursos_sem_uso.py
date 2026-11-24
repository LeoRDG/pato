"""Sem assets velhos (tools/t184_sem_recursos_sem_uso.py): todo recurso do jogo é usado em algum lugar, todo arquivo
versionado em assets/ é de algum recurso, e as fontes (tiles 1x, gravações originais) ficam em fontes/, fora da main."""
import json, os, subprocess, unittest

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def strings(x):
    if isinstance(x, str):
        yield x
    elif isinstance(x, dict):
        for v in x.values():
            yield from strings(v)
    elif isinstance(x, list):
        for v in x:
            yield from strings(v)


class SemRecursosSemUso(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.d = json.load(open(os.path.join(RAIZ, 'jogo.json'), encoding='utf-8'))
        cls.rec = cls.d['resources']['resources']

    def test_todo_recurso_e_usado(self):
        texto = '\n'.join(strings({k: v for k, v in self.d.items() if k != 'resources'}))
        self.assertEqual([r['name'] for r in self.rec if r['name'] not in texto], [])

    def test_todo_arquivo_de_assets_e_de_um_recurso(self):
        versionados = subprocess.run(['git', 'ls-files', 'assets'], cwd=RAIZ, capture_output=True,
                                     text=True).stdout.splitlines()
        arquivos = {r['file'] for r in self.rec}
        self.assertEqual([f for f in versionados if f not in arquivos], [])
        for r in self.rec:
            self.assertTrue(os.path.exists(os.path.join(RAIZ, r['file'])), r['file'])

    def test_fontes_fora_de_assets(self):
        for f in ('fontes/fontes_cc0/FONTES.txt', 'fontes/ceu/tiles/tiles_ceu.png',
                  'fontes/gandalf_hell/tiles/tiles_inferno.png', 'fontes/purgatorio/tiles/tiles_purgatorio.png'):
            self.assertTrue(os.path.exists(os.path.join(RAIZ, f)), f)
        self.assertNotIn('fontes/', json.dumps(self.d))


if __name__ == '__main__':
    unittest.main()
