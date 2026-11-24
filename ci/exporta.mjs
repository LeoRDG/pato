// Exporta o jogo para HTML5 (a mesma exportação "Web" do GDevelop), sem abrir o editor.
// Uso: node ci/exporta.mjs jogo.json pasta_de_saida
// A versão do núcleo do GDevelop está em ci/package.json; mantenha igual à do editor (gdVersion no jogo.json).
import { loadProject, exportProject } from "gdcore-tools";
import { readFileSync, writeFileSync } from "node:fs";
import { join } from "node:path";

// Quantas imagens/sons o jogo baixa ao mesmo tempo enquanto carrega. O GDevelop usa 20; com ~1200 imagens isso dá
// ~60 rodadas de ida e volta ao servidor antes do menu. O GitHub Pages usa HTTP/2 (uma conexão só para tudo),
// então dá para pedir bem mais de uma vez.
const DOWNLOADS_SIMULTANEOS = Number(process.env.DOWNLOADS_SIMULTANEOS || 100);

const [, , projeto, saida] = process.argv;
if (!projeto || !saida) {
  console.error("uso: node ci/exporta.mjs jogo.json pasta_de_saida");
  process.exit(1);
}
const p = await loadProject(projeto);
await exportProject(p, saida);

const carregador = join(saida, "ResourceLoader.js");
const js = readFileSync(carregador, "utf8");
const LIMITE = /maxForegroundConcurrency=\d+/;
if (!LIMITE.test(js)) {
  // o GDevelop mudou o ResourceLoader: melhor falhar do que publicar sem perceber o carregamento lento
  console.error("não achei maxForegroundConcurrency em", carregador);
  process.exit(1);
}
writeFileSync(carregador, js.replace(LIMITE, `maxForegroundConcurrency=${DOWNLOADS_SIMULTANEOS}`));
console.log("downloads simultâneos ao carregar:", DOWNLOADS_SIMULTANEOS);
console.log("exportado:", p.getName(), "-", p.getLayoutsCount(), "cenas ->", saida);
