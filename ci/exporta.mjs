// Exporta o jogo para HTML5 (a mesma exportação "Web" do GDevelop), sem abrir o editor.
// Uso: node ci/exporta.mjs jogo.json pasta_de_saida
// A versão do núcleo do GDevelop está em ci/package.json; mantenha igual à do editor (gdVersion no jogo.json).
import { loadProject, exportProject } from "gdcore-tools";

const [, , projeto, saida] = process.argv;
if (!projeto || !saida) {
  console.error("uso: node ci/exporta.mjs jogo.json pasta_de_saida");
  process.exit(1);
}
const p = await loadProject(projeto);
await exportProject(p, saida);
console.log("exportado:", p.getName(), "-", p.getLayoutsCount(), "cenas ->", saida);
