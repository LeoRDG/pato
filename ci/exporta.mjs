// Exporta o jogo para HTML5 (a mesma exportação "Web" do GDevelop), sem abrir o editor.
// Uso: node ci/exporta.mjs jogo.json pasta_de_saida
// A versão do núcleo do GDevelop está em ci/package.json; mantenha igual à do editor (gdVersion no jogo.json).
import { loadProject, exportProject } from "gdcore-tools";
import { readFileSync, writeFileSync } from "node:fs";
import { join } from "node:path";

// Quantas imagens/sons o jogo baixa ao mesmo tempo enquanto carrega. O GDevelop usa 20; com ~1200 imagens isso dá
// ~60 rodadas de ida e volta ao servidor antes do menu. A Cloudflare usa HTTP/2 e HTTP/3 (uma conexão só para tudo),
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

// Celular: aberto pela tela de início ("Adicionar à tela de início"), o jogo abre sem a barra do navegador.
// No Android o manifesto pede tela cheia (o GDevelop exporta "standalone"); no iPhone, onde o Safari não tem tela
// cheia para páginas, o atalho da tela de início é o jeito de jogar sem as barras (apple-mobile-web-app-capable, que o
// GDevelop já põe). Se o GDevelop mudar esses arquivos, só avisa: o jogo funciona do mesmo jeito.
const manifesto = join(saida, "manifest.webmanifest");
try {
  const m = JSON.parse(readFileSync(manifesto, "utf8"));
  m.display = "fullscreen";
  m.display_override = ["fullscreen", "standalone"];
  m.orientation = "landscape";
  writeFileSync(manifesto, JSON.stringify(m, null, 2));
} catch (e) {
  console.warn("aviso: não ajustei", manifesto, "-", e.message);
}
const pagina = join(saida, "index.html");
const html = readFileSync(pagina, "utf8");
if (html.includes("apple-mobile-web-app-capable") && !html.includes('name="mobile-web-app-capable"')) {
  writeFileSync(pagina, html.replace(/(<meta name="apple-mobile-web-app-capable"[^>]*>)/,
    '$1\n    <meta name="mobile-web-app-capable" content="yes">'));
} else if (!html.includes('name="mobile-web-app-capable"')) {
  console.warn("aviso: não achei apple-mobile-web-app-capable em", pagina);
}
console.log("exportado:", p.getName(), "-", p.getLayoutsCount(), "cenas ->", saida);
