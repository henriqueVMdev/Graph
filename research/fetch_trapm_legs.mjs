// Extrai os trades (legs) da estrategia TrapM/MM9-LW do reportData do
// TradingView via CDP e salva em research/data/trapm_legs.json.
// Uso: node research/fetch_trapm_legs.mjs
import CDP from '../tradingview-mcp/node_modules/chrome-remote-interface/index.js';
import { writeFileSync } from 'fs';
import { fileURLToPath } from 'url';
import { dirname, join } from 'path';

const EXPR = `(() => {
  const chart = window.TradingViewApi._activeChartWidgetWV.value()._chartWidget;
  const sources = chart.model().model().dataSources();
  for (const s of sources) {
    let mi = null;
    try { mi = s.metaInfo ? s.metaInfo() : null; } catch (e) {}
    if (mi && (mi.isTVScriptStrategy || mi.is_strategy) && /LW/i.test(mi.description)) {
      let rd = s.reportData();
      if (rd && typeof rd.value === 'function') rd = rd.value();
      const code = c => c.includes('TP1') ? 1 : c.includes('TP2') ? 2 : 3;
      return JSON.stringify(rd.trades.map(t => [
        t.e.tm, t.e.p, t.q, t.e.c.startsWith('Long') ? 1 : -1,
        t.x ? t.x.tm : 0, t.x ? t.x.p : 0, t.x ? code(t.x.c) : 0,
      ]));
    }
  }
  return 'null';
})()`;

const targets = await CDP.List({ port: 9222 });
const page = targets.find(t => t.type === 'page' && /tradingview\.com\/chart/i.test(t.url));
if (!page) { console.error('aba do chart nao encontrada'); process.exit(1); }
const client = await CDP({ target: page });
const { result } = await client.Runtime.evaluate({ expression: EXPR, returnByValue: true });
await client.close();

const out = join(dirname(fileURLToPath(import.meta.url)), 'data', 'trapm_legs.json');
writeFileSync(out, result.value);
console.log('salvo:', out, '|', JSON.parse(result.value).length, 'legs');
