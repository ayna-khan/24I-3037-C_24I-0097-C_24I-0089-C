/* The Lifeline Gazette: talks to the project's JSON API and prints the results. */
'use strict';

const SCENARIOS = { 1: 'Delta Flood', 2: 'Mountain Earthquake', 3: 'Coastal Cyclone', 4: 'Urban Flash Flood', 5: 'Landslide Corridor', 6: 'Outbreak Camp' };
const CATEGORIES = ['Food', 'Water', 'Medicine', 'Tools', 'Rare'];
const METHOD_NAMES = {
  dp: 'dynamic programming', greedy: 'greedy', dijkstra: 'Dijkstra', bellman: 'Bellman-Ford', bfs: 'breadth-first search',
  dpquad: 'quadratic DP', heap: 'binary heap', scan: 'linear scan', fifo: 'first come, first served',
  kruskal: 'Kruskal', prim: 'Prim', memo: 'memoised recursion', brute: 'brute force',
};
const CHECK_NAMES = {
  reachability: 'Reachable locations', route_open_roads_and_cost: 'Route uses open roads; cost adds up',
  capacity_and_load_value: 'Load fits the truck; value adds up', rescue_availability_compatibility_and_total: 'Rescue windows available and compatible',
  alarm_order_and_release_ticks: 'Alarm order and ticks', cable_tree_connects_hq_component: 'Cable tree connects HQ’s region',
  chain_bracketing_cost: 'Pipeline bracketing cost', drum_length_and_price: 'Drum cut length and price',
};
const POLICIES = [['optimized', 'Our engine', '#a8322a'], ['baseline', 'Algorithm baselines', '#1f68a8'], ['simple', 'Simple policies', '#a87a12']];

const state = { cases: [], meta: null, data: null, day: 1, page: 'front', campaigns: {}, token: 0 };
const $ = id => document.getElementById(id);
const esc = v => String(v).replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
const num = v => v === null || v === undefined ? '—' : Number(v).toLocaleString('en-US', { maximumFractionDigits: 2 });
const fact = (k, v) => `<div><dt>${k}</dt><dd>${v}</dd></div>`;
const figure = (value, label) => `<div class="figure"><b>${value}</b><span>${label}</span></div>`;
const table = (head, rows) => `<table><thead><tr>${head.map(h => `<th>${h}</th>`).join('')}</tr></thead><tbody>${rows.map(r => `<tr>${r.map(c => `<td>${c}</td>`).join('')}</tr>`).join('')}</tbody></table>`;
const short = (list, limit = 14) => list.length <= limit ? list.join(' → ') : `${list.slice(0, limit / 2).join(' → ')} → … → ${list.slice(-limit / 2).join(' → ')}`;

function status(text, error = false) {
  $('status').textContent = text;
  $('status').classList.toggle('error', error);
}

async function api(path, body) {
  const response = await fetch(path, body ? { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) } : {});
  const data = await response.json();
  if (!response.ok) throw new Error(data.note || data.status || response.statusText);
  return data;
}

/* ---------- case selection ---------- */
function filteredCases() {
  const tier = $('tierFilter').value, scenario = $('scenarioFilter').value;
  return state.cases.filter(c => (!tier || c.tier === tier) && (!scenario || c.scenario === Number(scenario)));
}

function fillCaseList() {
  const found = filteredCases();
  $('caseList').innerHTML = found.slice(0, 400).map(c => `<option value="${esc(c.case_id)}">${c.tier} · ${SCENARIOS[c.scenario] || ''}</option>`).join('');
  $('matchCount').textContent = `${found.length.toLocaleString('en-US')} cases`;
}

async function loadCase(id) {
  const token = ++state.token;
  const meta = state.cases.find(c => c.case_id === id);
  if (!meta) { status(`No case called “${id}” in the dataset.`, true); return; }
  status(`Setting the type for case ${id}…`);
  try {
    const data = await api('/case', { case_id: id });
    const campaign = await api('/campaign', { case_id: id });
    if (token !== state.token) return;
    Object.assign(state, { meta, data, campaigns: { optimized: campaign } });
    $('caseId').value = id;
    $('dateline').textContent = `Case ${id} · ${SCENARIOS[meta.scenario] || 'Scenario ' + meta.scenario} · Tier ${meta.tier}`;
    $('conditions').innerHTML = `<b>${SCENARIOS[meta.scenario] || ''}</b><br>${num(data.locations.length)} locations · ${num(data.roads.length)} roads<br>Truck: ${num(meta.capacity)} kg`;
    status('');
    renderAll();
  } catch (error) {
    if (token === state.token) status(`The presses jammed: ${error.message}`, true);
  }
}

function renderAll() {
  renderDays();
  renderEdition();
  renderWeek();
  renderMaps();
  renderWorks();
}

/* ---------- front page ---------- */
function renderDays() {
  $('days').innerHTML = state.campaigns.optimized.days.map(d =>
    `<button data-day="${d.day}" class="${d.day === state.day ? 'on' : ''}">Day ${d.day}<span>${esc(d.event)}</span></button>`).join('');
}

function headline(d) {
  const place = `Location ${d.target}`;
  if (d.route.status !== 'OK') return [`${place} cut off`, `No open road leads from headquarters. The ${d.trip_kind === 'evacuation' ? 'evacuation' : 'convoy'} is held; rescue and alarm desks carry on.`];
  if (d.trip_kind === 'evacuation') return [`Evacuation route holds to ${place}`, `An empty convoy makes the run in ${num(d.route.cost)} cost units over ${d.route.road_ids.length} road(s), with ${d.closed_roads.length} closed.`];
  const titles = {
    Normal: `Relief rolls to ${place}`, Storm: `Storm slows the roads; ${place} still reached`,
    'Food shortage': `Food runs short: convoy makes for ${place}`, 'Dangerous area': `Convoy threads danger zone to ${place}`,
    'Medical emergency': `Medicine rushed to ${place}`, Flood: `Convoy beats the flood to ${place}`,
  };
  const load = d.load && d.load.selected.length
    ? `${d.load.selected.length} crates worth ${num(d.load.total_value)} travel at a route cost of ${num(d.route.cost)}.`
    : `No crates could be loaded; the route would cost ${num(d.route.cost)}.`;
  return [titles[d.event] || `${esc(d.event)}: convoy to ${place}`, load];
}

function leadStory(d) {
  const meta = state.meta, parts = [];
  parts.push(d.route.status === 'OK'
    ? `Headquarters dispatched its planners at daybreak with ${place(d.target)} on the board. ${METHOD_NAMES[d.methods.B]} found a way through ${d.route.road_ids.length} road(s) at a total cost of ${num(d.route.cost)}, counting both travel minutes and the penalty of each place entered.`
    : `Headquarters had ${place(d.target)} on the board, but ${METHOD_NAMES[d.methods.B]} found no open path. Only ${d.route.reachable.length} of ${state.data.locations.length} locations remain within reach.`);
  if (d.route.status === 'OK' && d.route.fewest_cost !== null && d.route.fewest_cost > d.route.cost) {
    parts.push(`The route with the fewest roads (${d.route.fewest_path.length - 1}) would have cost ${num(d.route.fewest_cost)}, or ${num(d.route.fewest_cost / d.route.cost)} times as much.`);
  }
  if (d.load) {
    parts.push(d.load.status === 'OK'
      ? `At the depot, ${METHOD_NAMES[d.methods.A]} filled ${num(d.load.total_weight)} of ${num(d.input.capacity)} kg with ${d.load.selected.length} of ${num(d.input.counts.crates)} crates, for a value of ${num(d.load.total_value)}.`
      : `The depot loaded nothing: ${esc(d.load.note || d.load.status)}.`);
  } else if (d.trip_kind !== 'evacuation') {
    parts.push('With no way to deliver, the crates stayed in the depot.');
  } else {
    parts.push('Under standing orders, no cargo was loaded on the evacuation run.');
  }
  parts.push(`Rescue teams booked ${d.rescue.chosen.length} windows worth ${num(d.rescue.total)}, while the emergency desk answered ${num(d.alarms.releases.length)} alarms in the ${esc(meta.case_id)} log.`);
  return parts.map(p => `<p>${p.charAt(0).toUpperCase() + p.slice(1)}</p>`).join('');
}
function place(id) { return `Location ${id}`; }

function conditions(d) {
  const input = d.input;
  const rows = [fact('Roads closed', `${d.closed_roads.length} of ${num(input.counts.roads)}`)];
  const slowed = Object.keys(input.changed_minutes).length, risky = Object.keys(input.changed_penalties).length;
  if (slowed) rows.push(fact('Roads slowed', num(slowed)));
  if (risky) rows.push(fact('Penalties raised', num(risky)));
  for (const [cat, m] of Object.entries(input.multipliers)) rows.push(fact(`${CATEGORIES[cat]} value`, `× ${m}`));
  for (const a of input.extra_alarms) rows.push(fact('Extra alarm', `priority ${a.priority}`));
  rows.push(fact('Rescue windows open', num(input.counts.windows)), fact('Alarms on file', num(input.counts.alarms)));
  return `<dl class="facts">${rows.join('')}</dl>`;
}

function dayCrates(d) {
  const picked = new Set(d.load.selected);
  return state.data.crates.filter(c => picked.has(c[0]))
    .map(([id, cat, weight, value]) => [id, CATEGORIES[cat], weight, value * (d.input.multipliers[cat] ?? 1)]);
}

function manifest(d) {
  if (!d.load) return `<p class="lead">No manifest today: ${d.trip_kind === 'evacuation' ? 'evacuation runs without cargo.' : 'the target cannot be reached.'}</p>`;
  const crates = dayCrates(d), share = d.input.capacity ? 100 * d.load.total_weight / d.input.capacity : 0;
  return `<div class="meter" role="img" aria-label="Truck ${num(share)} percent full"><i style="width:${share}%"></i></div>
    <p class="small">${num(d.load.total_weight)} of ${num(d.input.capacity)} kg · value ${num(d.load.total_value)} · ${METHOD_NAMES[d.methods.A]}</p>
    <div class="scroll">${table(['Crate', 'Kind', 'kg', 'Value'], crates.slice(0, 200))}</div>
    ${crates.length > 200 ? `<p class="small">First 200 of ${num(crates.length)} loaded crates.</p>` : ''}`;
}

function dispatches(d) {
  const alarms = new Map(state.data.alarms.map(a => [a[0], { tick: a[1], priority: a[2] }]));
  for (const a of d.input.extra_alarms) alarms.set(a.alarm_id, a);
  const rows = d.alarms.releases.slice(0, 100).map(([id, tick]) => {
    const a = alarms.get(id) || {};
    return [tick, `#${id}`, a.priority ?? '—', tick - (a.tick ?? tick)];
  });
  return `<dl class="facts">${fact('Longest wait', `${num(d.alarms.max_wait)} ticks`)}${fact('Largest backlog', num(d.alarms.max_backlog))}${fact('Urgent (9–10) mean wait', num(d.alarm_metrics.urgent_wait / Math.max(1, d.alarm_metrics.urgent_count)))}</dl>
    <div class="scroll">${table(['Tick', 'Alarm', 'Priority', 'Waited'], rows)}</div>
    <p class="small">First ${rows.length} answers, by ${METHOD_NAMES[d.methods.D]}.</p>`;
}

function timetable(d) {
  const chosen = new Set(d.rescue.chosen);
  const windows = state.data.windows.filter(w => chosen.has(w[0])).sort((a, b) => a[1] - b[1]);
  return {
    windows,
    html: `<div id="timeline"></div>
      <p class="small">${windows.length} compatible windows, total value ${num(d.rescue.total)}, by ${METHOD_NAMES[d.methods.C]}. Black blocks are booked time.</p>
      <div class="scroll">${table(['Window', 'From', 'To', 'Value'], windows.slice(0, 200).map(([id, s, f, v]) => [id, clock(s), clock(f), v]))}</div>`,
  };
}
const clock = m => `${String(Math.floor(m / 60)).padStart(2, '0')}:${String(m % 60).padStart(2, '0')}`;

function publicWorks(d) {
  if (!d.network) return '';
  const pieces = d.drum.pieces || [];
  return `<h2 class="headline">Rebuilding begins</h2>
    <p class="deck">The final-day review: new cable for the region HQ can still reach, and the pipeline works.</p>
    <div class="columns three">
      <div><h3 class="kicker">Cable network (F)</h3>
        <div class="figures">${figure(num(d.network.cost), 'cable cost')}${figure(num(d.network.road_ids.length), 'roads cabled')}</div>
        <p>${METHOD_NAMES[d.methods.F]} connects the ${num(d.route.reachable.length)} locations still reachable from headquarters.</p></div>
      <div><h3 class="kicker">Pipeline chain (G)</h3>
        <div class="figures">${figure(num(d.chain.cost), 'multiplications')}${figure(num(state.data.dims.length - 1), 'matrices')}</div>
        <div class="bracketing">${esc(d.chain.bracketing || d.chain.note)}</div></div>
      <div><h3 class="kicker">Pipe drum (G)</h3>
        <div class="figures">${figure(num(d.drum.price), 'sale price')}${figure(num(pieces.length), 'pieces')}</div>
        ${drumBar(pieces)}<p class="small">Each block is one piece of the cut drum.</p></div>
    </div>`;
}

function drumBar(pieces) {
  if (!pieces.length) return '';
  const total = pieces.reduce((a, b) => a + b, 0), shown = pieces.slice(0, 120);
  return `<div class="drum">${shown.map(p => `<i style="flex:${p}" title="length ${p}">${p / total > 0.05 ? p : ''}</i>`).join('')}${pieces.length > 120 ? `<i style="flex:${total - shown.reduce((a, b) => a + b, 0)}">…</i>` : ''}</div>`;
}

function renderEdition() {
  const d = state.campaigns.optimized.days[state.day - 1];
  const [title, deck] = headline(d);
  const rescue = timetable(d);
  const checks = Object.entries(d.checks), passed = checks.every(([, ok]) => ok !== false);
  $('edition').innerHTML = `
    <h2 class="headline">${title}</h2>
    <p class="deck">${deck}</p>
    <p class="byline">Day ${d.day} of 7 · ${esc(d.event)} · From the Gazette’s dispatch desk</p>
    <div class="columns front">
      <div><h3 class="kicker">The lead</h3><div class="lead">${leadStory(d)}</div></div>
      <div><figure><div class="map-box" id="frontMap"></div><figcaption id="frontCaption"></figcaption></figure>${mapLegend(false)}
        ${d.route.status === 'OK' ? `<p class="small centre">Itinerary: ${short(d.route.path.map(v => v === 0 ? 'HQ' : v))}</p>` : ''}</div>
      <div><h3 class="kicker">Conditions</h3>${conditions(d)}
        <div class="figures">${figure(num(d.route.cost), 'route cost')}${figure(d.load ? num(d.load.total_value) : '—', 'load value')}${figure(num(d.rescue.total), 'rescue value')}${figure(num(d.alarms.total_wait), 'total alarm wait')}</div>
        <span class="stamp ${passed ? '' : 'bad'}">${passed ? 'Verified' : 'Check failed'}</span>
        <ul class="checks">${checks.map(([k]) => `<li>${CHECK_NAMES[k] || esc(k)}</li>`).join('')}</ul></div>
    </div>
    <div class="columns three">
      <div><h3 class="kicker">The manifest (A)</h3>${manifest(d)}</div>
      <div><h3 class="kicker">Emergency dispatches (D)</h3>${dispatches(d)}</div>
      <div><h3 class="kicker">Rescue timetable (C)</h3>${rescue.html}</div>
    </div>
    ${publicWorks(d)}`;
  Draw.timeline($('timeline'), rescue.windows);
  const drawn = Draw.map($('frontMap'), {
    data: state.data, caseId: state.meta.case_id, closed: d.closed_roads, path: d.route.path, routeRoads: d.route.road_ids,
    cable: d.network ? d.network.road_ids : [], reachable: d.route.reachable, target: d.target,
  });
  $('frontCaption').textContent = mapCaption(drawn);
}

function mapCaption(drawn) {
  return drawn.partial
    ? `Schematic detail: ${drawn.shown} of ${num(state.data.locations.length)} locations, around the route. Positions are not geographic.`
    : 'Schematic map of the whole district. Positions are not geographic. Hover for details.';
}

function mapLegend(cable) {
  return `<div class="legend"><span><i class="dot" style="background:#1d1a15;border-radius:0"></i>HQ</span><span><i class="dot" style="background:#a8322a"></i>Target</span>
    <span><i class="dot" style="background:#cabfa6"></i>Cut off</span><span><i style="background:#1d1a15"></i>Route</span>
    <span><i style="background:repeating-linear-gradient(90deg,#a8322a 0 5px,transparent 5px 9px)"></i>Closed road</span>
    ${cable || state.day === 7 ? '<span><i style="background:#1f68a8"></i>Cable</span>' : ''}</div>`;
}

/* ---------- week in review ---------- */
const SERIES = [
  ['Load value delivered', d => d.load ? d.load.total_value : null, 'Higher is better. A dash means nothing was loaded.'],
  ['Route cost', d => d.route.status === 'OK' ? d.route.cost : null, 'Lower is better. A dash means the target was cut off.'],
  ['Rescue value booked', d => d.rescue.total, 'Higher is better.'],
  ['Urgent alarms: mean wait', d => d.alarm_metrics.urgent_wait / Math.max(1, d.alarm_metrics.urgent_count), 'Ticks, priorities 9–10. Lower is better.'],
];

function renderWeek() {
  const report = state.campaigns.optimized, s = report.summary;
  const compared = POLICIES.every(([key]) => state.campaigns[key]);
  const shown = compared ? POLICIES : POLICIES.slice(0, 1);
  const rows = report.days.map(d => [d.day, esc(d.event), d.target, d.closed_roads.length, esc(d.dispatch_status.replace('_', ' ')),
    d.route.status === 'OK' ? num(d.route.cost) : '—', d.load ? num(d.load.total_value) : '—', num(d.rescue.total), num(d.alarms.total_wait)]);
  $('weekBody').innerHTML = `
    <h2 class="headline">Seven days in the field</h2>
    <p class="deck">Case ${esc(report.case_id)}: ${num(s.delivered_value)} in relief delivered, ${s.unreachable_days} day(s) with the target cut off.</p>
    <p class="byline">The official calendar, run by our engine</p>
    <div class="figures" style="grid-template-columns:repeat(auto-fit,minmax(150px,1fr))">
      ${figure(num(s.delivered_value), 'value delivered')}${figure(num(s.route_cost), 'total route cost')}${figure(num(s.rescue_total), 'rescue value')}${figure(num(s.urgent_mean_wait), 'urgent mean wait')}${figure(s.evacuation_cost === null ? '—' : num(s.evacuation_cost), 'evacuation cost')}</div>
    <div class="wide">${table(['Day', 'Event', 'Target', 'Closed', 'Trip', 'Route cost', 'Load value', 'Rescue', 'Alarm wait'], rows)}</div>
    <p class="centre" style="margin:18px 0">${compared ? '' : '<button id="compare">Compare with the rival methods</button><br><span class="small">Runs the week twice more. Large cases can take a while.</span>'}</p>
    ${compared ? `<h3 class="kicker">Our engine against its rivals</h3>
      <div class="legend">${POLICIES.map(([, name, color]) => `<span><i style="background:${color}"></i>${name}</span>`).join('')}</div>` : ''}
    <div class="columns two">${SERIES.map(([name, , note], i) => `<figure style="margin-bottom:14px"><h3 class="kicker">${name}</h3><div id="chart${i}"></div><figcaption>${note}</figcaption></figure>`).join('')}</div>
    ${compared ? `<div class="wide">${table(['Week total', ...POLICIES.map(p => p[1])], [
      ['Value delivered', 'delivered_value'], ['Route cost', 'route_cost'], ['Rescue value', 'rescue_total'], ['Total alarm wait', 'alarm_wait'], ['Urgent mean wait', 'urgent_mean_wait'], ['Days cut off', 'unreachable_days'],
    ].map(([name, key]) => [name, ...POLICIES.map(([p]) => num(state.campaigns[p].summary[key]))]))}</div>
    <p class="small">“Algorithm baselines” solve B, C, D, F and G exactly by a second method and load greedily. “Simple policies” are shortcuts that are not meant to be optimal: fewest-roads routing, greedy choices and a first-come-first-served alarm queue.</p>` : ''}`;
  SERIES.forEach(([, get], i) => Draw.bars($('chart' + i), report.days.map(d => d.day),
    shown.map(([key, name, color]) => ({ name, color, values: state.campaigns[key].days.map(get) })), v => num(v)));
  const button = $('compare');
  if (button) button.addEventListener('click', compare);
}

async function compare() {
  const token = state.token, id = state.meta.case_id, campaigns = state.campaigns;
  $('compare').disabled = true;
  try {
    for (const [policy, name] of POLICIES.slice(1)) {
      status(`Running the week with ${name.toLowerCase()}…`);
      const report = await api('/campaign', { case_id: id, policy });
      if (token !== state.token) return;
      campaigns[policy] = report;
    }
    status('');
    renderWeek();
  } catch (error) {
    status(`Comparison failed: ${error.message}`, true);
    $('compare').disabled = false;
  }
}

/* ---------- map room (B and F) ---------- */
const room = { closed: new Set(), request: 0 };

function renderMaps() {
  const { data, meta } = state;
  room.closed = new Set();
  const waves = Object.keys(data.waves).map(Number).sort((a, b) => a - b);
  const targets = [...new Set([meta.target_0, meta.target_1, meta.target_2])];
  $('mapsBody').innerHTML = `
    <h2 class="headline">The Map Room</h2>
    <p class="deck">Close a road, change the method, and watch the route and the cable plan answer. Base road times and penalties.</p>
    <p class="byline">Modules B and F, live</p>
    <div class="columns map">
      <div><figure><div class="map-box" id="roomMap"></div><figcaption id="roomCaption"></figcaption></figure>${mapLegend(true)}</div>
      <div><h3 class="kicker">Orders</h3>
        <div class="controls stack">
          <label>Target <input id="target" type="number" min="0" max="${data.locations.length - 1}" value="${meta.target_0}" list="targets"></label>
          <datalist id="targets">${targets.map(t => `<option value="${t}">`).join('')}</datalist>
          <label>Route by <select id="routeMethod"><option value="dijkstra">Dijkstra</option><option value="bellman">Bellman-Ford</option><option value="bfs">Fewest roads (BFS)</option></select></label>
          <label>Cable by <select id="cableMethod"><option value="">Hide cable</option><option value="kruskal">Kruskal</option><option value="prim">Prim</option></select></label>
          <label>Close road no. <input id="roadNo" type="number" min="0"><button id="toggleRoad" type="button">Toggle</button></label>
        </div>
        <div class="controls">${waves.map(w => `<button type="button" data-wave="${w}">Wave ${w}</button>`).join('')}<button type="button" id="reopen">Reopen all</button></div>
        <div id="roomResult"></div></div>
    </div>`;
  for (const id of ['target', 'routeMethod', 'cableMethod']) $(id).addEventListener('change', planRoute);
  $('toggleRoad').addEventListener('click', () => { if ($('roadNo').value !== '') toggleRoad(Number($('roadNo').value)); });
  $('reopen').addEventListener('click', () => { room.closed.clear(); planRoute(); });
  $('mapsBody').querySelectorAll('[data-wave]').forEach(button => button.addEventListener('click', () => {
    const ids = data.waves[button.dataset.wave], all = ids.every(r => room.closed.has(r));
    ids.forEach(r => all ? room.closed.delete(r) : room.closed.add(r));
    planRoute();
  }));
  planRoute();
}

function toggleRoad(no) {
  room.closed.has(no) ? room.closed.delete(no) : room.closed.add(no);
  planRoute();
}

async function planRoute() {
  const request = ++room.request, token = state.token;
  const { data, meta } = state;
  const target = Number($('target').value), method = $('routeMethod').value, cableMethod = $('cableMethod').value;
  const blocked = [...room.closed];
  try {
    const route = await api('/route', { case_id: meta.case_id, target, method, blocked });
    const net = cableMethod ? await api('/network', { case_id: meta.case_id, blocked, method: cableMethod }) : null;
    if (request !== room.request || token !== state.token) return;
    status('');
    const drawn = Draw.map($('roomMap'), {
      data, caseId: meta.case_id, closed: blocked, path: route.path, routeRoads: route.road_ids,
      cable: net ? net.road_ids : [], reachable: route.reachable, target, onRoad: toggleRoad,
    });
    $('roomCaption').textContent = mapCaption(drawn) + ' Click a road to close it.';
    const rows = [fact('Result', route.status === 'OK' ? 'Route found' : 'No route'), fact('Travel cost', num(route.cost)),
      fact('Roads on route', route.status === 'OK' ? route.road_ids.length : '—'),
      fact('Fewest-roads route cost', num(route.fewest_cost)), fact('Reachable', `${num(route.reachable.length)} of ${num(data.locations.length)}`),
      fact('Roads closed', blocked.length)];
    if (net) rows.push(fact('Cable cost (HQ’s region)', num(net.cost)), fact('Cable roads', num(net.road_ids.length)));
    $('roomResult').innerHTML = `<dl class="facts">${rows.join('')}</dl>
      ${route.status === 'OK' ? `<p class="small">${short(route.path.map(v => v === 0 ? 'HQ' : v))}</p>` : ''}
      ${route.note ? `<p class="small">${esc(route.note)}.</p>` : ''}`;
  } catch (error) {
    if (request === room.request) status(`Map room: ${error.message}`, true);
  }
}

/* ---------- works desk (G) ---------- */
function renderWorks() {
  const { data } = state;
  const options = list => list.map(m => `<option value="${m}">${METHOD_NAMES[m]}</option>`).join('');
  $('worksBody').innerHTML = `
    <h2 class="headline">The Works Desk</h2>
    <p class="deck">The order of pipeline multiplications and the most profitable way to cut a drum of pipe.</p>
    <p class="byline">Module G, live</p>
    <div class="columns two">
      <div><h3 class="kicker">Pipeline chain: ${num(data.dims.length - 1)} matrices</h3>
        <div class="controls"><label>Method <select id="chainMethod">${options(['dp', 'memo', 'brute'])}</select></label><button id="runChain" type="button">Solve</button></div>
        <div id="chainOut"><p class="small">Brute force accepts at most 12 matrices.</p></div></div>
      <div><h3 class="kicker">Pipe drum: ${num(data.prices.length)} price lengths</h3>
        <div class="controls"><label>Method <select id="drumMethod">${options(['dp', 'memo', 'greedy', 'brute'])}</select></label>
          <label>Length <input id="drumLength" type="number" min="1" max="${data.prices.length}" value="${data.prices.length}"></label><button id="runDrum" type="button">Cut</button></div>
        <div id="drumOut"><p class="small">Brute force accepts lengths up to 20. Greedy is not always optimal.</p></div></div>
    </div>`;
  $('runChain').addEventListener('click', () => solveWork('chain', 'chainOut', { method: $('chainMethod').value }, r =>
    `<div class="figures">${figure(num(r.cost), 'scalar multiplications')}${figure(esc(r.status), 'status')}</div>
     <div class="bracketing">${esc(r.bracketing || r.note)}</div>`));
  $('runDrum').addEventListener('click', () => solveWork('drum', 'drumOut', { method: $('drumMethod').value, length: Number($('drumLength').value) }, r =>
    `<div class="figures">${figure(num(r.price), 'total price')}${figure(esc(r.status), 'status')}</div>
     ${drumBar(r.pieces || [])}<p class="small">${esc((r.pieces || []).slice(0, 60).join(' + '))}${(r.pieces || []).length > 60 ? ' + …' : ''}</p>
     ${r.note ? `<p class="small">${esc(r.note)}</p>` : ''}`));
}

async function solveWork(kind, out, args, print) {
  const token = state.token, box = $(out);
  box.innerHTML = '<p class="small">The desk is working…</p>';
  try {
    const result = await api('/' + kind, { case_id: state.meta.case_id, ...args });
    if (token === state.token) box.innerHTML = print(result);
  } catch (error) {
    box.innerHTML = `<p class="small">Could not solve: ${esc(error.message)}</p>`;
  }
}

/* ---------- start ---------- */
function showPage(page) {
  if (!$(page)) return;
  state.page = page;
  document.querySelectorAll('.page').forEach(s => s.classList.toggle('on', s.id === page));
  document.querySelectorAll('nav button').forEach(b => b.classList.toggle('on', b.dataset.page === page));
}

async function start() {
  $('nav').addEventListener('click', e => { if (e.target.dataset.page) showPage(e.target.dataset.page); });
  $('days').addEventListener('click', e => {
    const button = e.target.closest('[data-day]');
    if (!button) return;
    state.day = Number(button.dataset.day);
    renderDays();
    renderEdition();
  });
  $('caseForm').addEventListener('submit', e => { e.preventDefault(); loadCase($('caseId').value.trim()); });
  $('scenarioFilter').innerHTML += Object.entries(SCENARIOS).map(([k, v]) => `<option value="${k}">${v}</option>`).join('');
  for (const id of ['tierFilter', 'scenarioFilter']) $(id).addEventListener('change', () => {
    fillCaseList();
    const first = filteredCases()[0];
    if (first) $('caseId').value = first.case_id;
  });

  const query = new URLSearchParams(location.search);
  state.day = Math.min(7, Math.max(1, Number(query.get('day')) || 1));
  showPage(query.get('page') || 'front');
  status('Collecting the case list…');
  try {
    state.cases = await api('/cases');
    fillCaseList();
    await loadCase(query.get('case') || '41-00');
  } catch (error) {
    status(`Cannot reach the newsroom server: ${error.message}`, true);
  }
}

start();
