// Dependency-free checks of the report's JavaScript in a simulated DOM.
// This validates calculation and control logic; it does not claim browser layout QA.
// Usage: node scripts/validate_report.js
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const assert = require('node:assert/strict');

const root = path.resolve(__dirname, '..');
const html = fs.readFileSync(path.join(root, 'reports/flash_flood_report.html'), 'utf8');
const payload = html.match(/<script id="report-data" type="application\/json">([\s\S]*?)<\/script>/)[1];
const script = html.match(/<script>\s*([\s\S]*?)<\/script>/)[1];
const ids = [...html.matchAll(/\bid="([^"]+)"/g)].map(m => m[1]);
assert.equal(new Set(ids).size, ids.length, 'HTML IDs must be unique');
const elements = Object.fromEntries(ids.map(id => [id, {
  value: ['year', 'state'].includes(id) ? 'all' : id === 'population' ? 'full' : '',
  textContent: '', innerHTML: '', listeners: {}, options: [],
  add(option) { this.options.push(option); },
  addEventListener(event, fn) { this.listeners[event] = fn; },
} ]));
elements['report-data'].textContent = payload;
let lastBlob, clickedDownload = false;
const context = vm.createContext({
  console, Intl, Date, Map, Set, Math, Number, String, JSON,
  Option: function(text, value) { return {text, value}; },
  Blob: function(parts, options) { lastBlob = {parts, options}; return lastBlob; },
  URL: {createObjectURL() { return 'blob:test'; }, revokeObjectURL() {}},
  setTimeout(fn) { fn(); },
  document: {
    getElementById(id) { assert.ok(elements[id], `Unknown element ${id}`); return elements[id]; },
    createElement(type) { assert.equal(type, 'a'); return { click() { clickedDownload = true; } }; },
  },
});
vm.runInContext(script, context, {timeout: 10000});
assert.match(elements.cards.innerHTML, /19,191/);
assert.match(elements.cards.innerHTML, /\$8\.78B/);
assert.match(elements.cards.innerHTML, />389</);
assert.equal(elements.state.options.length, 51);
assert.equal(elements.year.options.length, 5);
assert.match(elements.trend.innerHTML, /2020/);
assert.match(elements.trend.innerHTML, /2024/);

elements.year.value = '2024'; elements.year.listeners.change();
assert.match(elements.cards.innerHTML, /4,459/);
assert.match(elements.cards.innerHTML, /\$3\.14B/);
elements.reset.listeners.click();
elements.population.value = 'routine'; elements.population.listeners.change();
assert.match(elements.cards.innerHTML, /18,012/);
assert.match(elements.cards.innerHTML, /\$422\.3M/);
elements.reset.listeners.click();
elements.state.value = 'DISTRICT OF COLUMBIA'; elements.state.listeners.change();
assert.match(elements.cards.innerHTML, />26</);
elements.reset.listeners.click();
elements.search.value = '970467'; elements.search.listeners.input();
assert.equal(elements.eventcount.textContent, '1 matching records');
assert.match(elements.eventrows.innerHTML, /TUSCALOOSA/);
elements.export.listeners.click();
assert.equal(clickedDownload, true);
const csv = lastBlob.parts.join('');
assert.match(csv, /970467/);
assert.equal(csv.split('\r\n').length, 2, 'CSV includes header plus exactly the searched record');
elements.search.value = '<no such county>'; elements.search.listeners.input();
assert.match(elements.eventrows.innerHTML, /No records match/);
elements.reset.listeners.click();
assert.equal(elements.filtermeta.textContent, '19,191 / 19,191 study events');
console.log('Report checks passed: initial KPIs, 60-month series, 51 state options, year filter, state filter, routine filter, search, empty state, reset, and CSV export.');
