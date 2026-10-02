// Independent of WebGL: the real public catalog remains usable on every device.
const panel = document.createElement('section');
panel.id = 'catalog-panel';
panel.innerHTML = `<details><summary>Explore public catalog <span id="catalog-count"></span></summary>
  <p id="catalog-state" role="status">Connecting to public Hugging Face metadata…</p>
  <p class="catalog-note">Provider RUNNING means hosted. App health, inference, training and proof validity are unverified. Lines show catalog membership, not governance or dependency proof.</p>
  <div class="catalog-filters"><label>Search <input id="catalog-search" type="search" placeholder="Name or namespace"></label>
  <label>Type <select id="catalog-kind"><option value="">All types</option><option selected>space</option><option>model</option><option>dataset</option></select></label>
  <label>Owner <select id="catalog-owner"><option value="">Both owners</option><option>SZLHOLDINGS</option><option>betterwithage</option></select></label></div>
  <div id="catalog-results"></div><details><summary>Freshness by source</summary><div id="catalog-sources"></div></details>
  <a href="/api/catalog" target="_blank" rel="noopener">Open catalog JSON ↗</a></details>`;
document.body.append(panel);
let catalog = null;
let unavailable = false;
function visibleNodes() {
  const query = document.getElementById('catalog-search').value.trim().toLowerCase();
  const kind = document.getElementById('catalog-kind').value;
  const owner = document.getElementById('catalog-owner').value;
  return (catalog?.nodes || []).filter(n => (!kind || n.kind === kind) && (!owner || n.owner === owner) && n.repo_id.toLowerCase().includes(query));
}
function draw() {
  const nodes = visibleNodes();
  document.getElementById('catalog-count').textContent = catalog ? `· ${nodes.length}/${catalog.nodes.length}` : '';
  document.getElementById('catalog-state').textContent = unavailable ? 'UNAVAILABLE · unable to refresh; displayed observations may be stale' : catalog ? `${catalog.state} · ${catalog.refreshing ? 'refresh in progress · ' : ''}checked ${new Date(catalog.served_at).toLocaleTimeString()} · cache ${catalog.ttl_seconds}s` : 'Connecting…';
  const results = document.getElementById('catalog-results');
  results.replaceChildren();
  for (const n of nodes) {
    const row = document.createElement('a');
    row.href = n.url; row.target = '_blank'; row.rel = 'noopener noreferrer';
    row.className = 'catalog-result';
    const current = !unavailable && n.observation_state === 'FRESH';
    row.dataset.stage = current ? n.runtime_stage : 'STALE';
    row.textContent = `${n.repo_id} ↗`;
    const detail = document.createElement('small');
    detail.textContent = `${n.kind} · ${n.runtime_stage === 'NOT_APPLICABLE' ? 'catalog only' : n.runtime_stage} · ${current ? 'FRESH' : unavailable ? 'STALE' : n.observation_state} · ${(n.revision || 'revision unknown').slice(0,12)}`;
    row.append(detail); results.append(row);
  }
  if (!nodes.length) results.textContent = catalog?.nodes.length ? 'No matching repositories.' : 'No public observations available yet.';
  const sources = document.getElementById('catalog-sources');
  sources.replaceChildren();
  for (const s of catalog?.sources || []) {
    const row = document.createElement('p');
    row.textContent = `${s.owner} / ${s.kind}: ${unavailable ? 'STALE / connection unavailable' : s.state} · ${s.observed_at ? new Date(s.observed_at).toLocaleString() : 'never observed'}${s.truncated ? ' · limited results' : ''}`;
    sources.append(row);
  }
  window.dispatchEvent(new CustomEvent('cosmos-catalog', {detail: {nodes: nodes.map(n => unavailable ? {...n, observation_state: 'STALE'} : n)}}));
}
for (const id of ['catalog-search', 'catalog-kind', 'catalog-owner']) document.getElementById(id).addEventListener('input', draw);
window.addEventListener('cosmos-catalog-request', draw);
async function refresh() {
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), 10000);
  try {
    const response = await fetch('/api/catalog', {signal: controller.signal, cache: 'no-store'});
    if (!response.ok) throw new Error('catalog unavailable');
    const data = await response.json();
    if (!Array.isArray(data.nodes) || !Array.isArray(data.sources)) throw new Error('invalid catalog');
    catalog = data; unavailable = false;
  } catch (_) { unavailable = true; }
  finally { clearTimeout(timeout); draw(); setTimeout(refresh, catalog?.refreshing ? 2000 : 30000); }
}
refresh();
