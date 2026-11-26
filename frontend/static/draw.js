/* SVG drawing: schematic road map, bar charts, rescue timetable. No libraries. */
'use strict';

const Draw = (() => {
  const NS = 'http://www.w3.org/2000/svg';
  const MAX_NODES = 260;
  const layouts = new Map();
  const KINDS = { D: 'Depot (HQ)', S: 'Shelter', H: 'Hospital', J: 'Junction' };

  function svg(tag, attrs = {}, parent) {
    const node = document.createElementNS(NS, tag);
    for (const [k, v] of Object.entries(attrs)) node.setAttribute(k, v);
    if (parent) parent.appendChild(node);
    return node;
  }

  function tip(node, text) {
    const box = document.getElementById('tip');
    node.addEventListener('mousemove', e => {
      box.textContent = text;
      box.hidden = false;
      box.style.left = Math.min(e.clientX + 14, innerWidth - box.offsetWidth - 8) + 'px';
      box.style.top = (e.clientY + 14) + 'px';
    });
    node.addEventListener('mouseleave', () => { box.hidden = true; });
  }

  /* Large maps keep the route (or HQ and target) and their nearest neighbours. */
  function pickNodes(data, path, target) {
    const all = data.locations.map(l => l[0]);
    if (all.length <= MAX_NODES) return { ids: all, partial: false };
    const near = new Map(all.map(v => [v, []]));
    for (const [, u, v] of data.roads) { near.get(u).push(v); near.get(v).push(u); }
    let seeds = path.length ? path : [0, target];
    if (seeds.length > MAX_NODES * 0.7) {
      const half = Math.floor(MAX_NODES * 0.35);
      seeds = seeds.slice(0, half).concat(seeds.slice(-half));
    }
    const chosen = new Set(seeds);
    const queue = [...chosen];
    for (let i = 0; i < queue.length && chosen.size < MAX_NODES; i++) {
      for (const v of near.get(queue[i])) {
        if (chosen.size >= MAX_NODES) break;
        if (!chosen.has(v)) { chosen.add(v); queue.push(v); }
      }
    }
    return { ids: [...chosen], partial: true };
  }

  /* Deterministic force-directed layout (Fruchterman-Reingold). */
  function layout(key, ids, roads) {
    if (layouts.has(key)) return layouts.get(key);
    const n = ids.length, at = new Map(ids.map((v, i) => [v, i]));
    const edges = roads.filter(r => at.has(r[1]) && at.has(r[2])).map(r => [at.get(r[1]), at.get(r[2])]);
    const near = ids.map(() => []);
    for (const [a, b] of edges) { near[a].push(b); near[b].push(a); }
    const order = [], seen = new Set();
    for (let s = 0; s < n; s++) {
      const stack = [s];
      while (stack.length) {
        const u = stack.pop();
        if (seen.has(u)) continue;
        seen.add(u); order.push(u);
        stack.push(...near[u]);
      }
    }
    const x = new Float64Array(n), y = new Float64Array(n);
    order.forEach((u, i) => {
      const angle = 2 * Math.PI * i / n, radius = 0.3 + 0.12 * ((i % 5) / 5);
      x[u] = 0.5 + radius * Math.cos(angle); y[u] = 0.5 + radius * Math.sin(angle);
    });
    const k = Math.sqrt(1 / Math.max(n, 1)), rounds = n > 150 ? 260 : 400;
    for (let step = 0; step < rounds; step++) {
      const dx = new Float64Array(n), dy = new Float64Array(n);
      for (let i = 0; i < n; i++) for (let j = i + 1; j < n; j++) {
        const ax = x[i] - x[j], ay = y[i] - y[j], d2 = ax * ax + ay * ay + 1e-6, f = k * k / d2;
        dx[i] += ax * f; dy[i] += ay * f; dx[j] -= ax * f; dy[j] -= ay * f;
      }
      for (const [a, b] of edges) {
        const ax = x[a] - x[b], ay = y[a] - y[b], f = Math.sqrt(ax * ax + ay * ay) / k;
        dx[a] -= ax * f; dy[a] -= ay * f; dx[b] += ax * f; dy[b] += ay * f;
      }
      const heat = 0.08 * (1 - step / rounds) + 0.001;
      for (let i = 0; i < n; i++) {
        dx[i] += (0.5 - x[i]) * 0.05; dy[i] += (0.5 - y[i]) * 0.05;
        const d = Math.hypot(dx[i], dy[i]) || 1, move = Math.min(d, heat);
        x[i] += dx[i] / d * move; y[i] += dy[i] / d * move;
      }
    }
    /* Turn the longest axis horizontal so the map fills a wide column. */
    const mx = x.reduce((a, b) => a + b, 0) / n, my = y.reduce((a, b) => a + b, 0) / n;
    let sxx = 0, syy = 0, sxy = 0;
    for (let i = 0; i < n; i++) {
      sxx += (x[i] - mx) ** 2; syy += (y[i] - my) ** 2; sxy += (x[i] - mx) * (y[i] - my);
    }
    const turn = -0.5 * Math.atan2(2 * sxy, sxx - syy);
    const rx = [...x].map((v, i) => (v - mx) * Math.cos(turn) - (y[i] - my) * Math.sin(turn));
    const ry = [...x].map((v, i) => (v - mx) * Math.sin(turn) + (y[i] - my) * Math.cos(turn));
    const lo = a => Math.min(...a), span = a => (Math.max(...a) - Math.min(...a)) || 1;
    const points = new Map(ids.map((v, i) => [v,
      [36 + (rx[i] - lo(rx)) / span(rx) * 728, 32 + (ry[i] - lo(ry)) / span(ry) * 416]]));
    layouts.set(key, points);
    return points;
  }

  /* opts: data, caseId, closed, path, routeRoads, cable, reachable, target, onRoad */
  function map(box, opts) {
    const { data, target } = opts;
    const closed = new Set(opts.closed), route = new Set(opts.routeRoads), cable = new Set(opts.cable || []);
    const reachable = opts.reachable ? new Set(opts.reachable) : null;
    const { ids, partial } = pickNodes(data, opts.path, target);
    const key = opts.caseId + (partial ? ':' + ids.join(',') : '');
    const points = layout(key, ids, data.roads);
    const root = svg('svg', { viewBox: '0 0 800 480', role: 'img', 'aria-label': 'Schematic road map' });
    const layers = ['plain', 'closed', 'cable', 'route'].map(() => svg('g', {}, root));
    const hits = svg('g', {}, root), dots = svg('g', {}, root);

    for (const [no, u, v, minutes, cost] of data.roads) {
      if (!points.has(u) || !points.has(v)) continue;
      const [x1, y1] = points.get(u), [x2, y2] = points.get(v), line = { x1, y1, x2, y2 };
      const kind = closed.has(no) ? 1 : route.has(no) ? 3 : cable.has(no) ? 2 : 0;
      svg('line', { ...line, class: 'road' + ['', ' closed', ' cable', ' route'][kind] }, layers[kind]);
      const hit = svg('line', { ...line, class: 'road-hit' + (opts.onRoad ? ' clickable' : '') }, hits);
      tip(hit, `Road ${no}: ${u} – ${v}\n${minutes} base minutes, cable cost ${cost}` +
        (closed.has(no) ? '\nCLOSED' : '') + (opts.onRoad ? '\nClick to close or reopen' : ''));
      if (opts.onRoad) hit.addEventListener('click', () => opts.onRoad(no));
    }
    if (ids.length > 150) root.classList.add('dense');
    const radius = ids.length > 150 ? 2.2 : ids.length > 60 ? 5 : 8;
    const onPath = new Set(opts.path);
    for (const [id, kind, penalty] of data.locations) {
      if (!points.has(id)) continue;
      const [cx, cy] = points.get(id);
      const special = id === 0 || id === target;
      let cls = 'node';
      if (reachable && !reachable.has(id)) cls += ' cut';
      if (id === 0) cls += ' hq';
      if (id === target) cls += ' target';
      const dot = svg(id === 0 ? 'rect' : 'circle', id === 0
        ? { x: cx - 8, y: cy - 8, width: 16, height: 16, class: cls }
        : { cx, cy, r: special ? Math.max(radius, 7) : radius, class: cls }, dots);
      tip(dot, `Location ${id} · ${KINDS[kind] || kind}\nBase penalty ${penalty}` +
        (reachable && !reachable.has(id) ? '\nCut off from HQ' : '') + (onPath.has(id) ? '\nOn the route' : ''));
      if (special || ids.length <= 60) {
        const label = svg('text', { x: cx, y: cy - radius - 5, class: 'node-label' + (special ? ' big' : '') }, dots);
        label.textContent = id === 0 ? 'HQ' : id === target ? `TARGET ${id}` : id;
      }
    }
    box.replaceChildren(root);
    return { partial, shown: ids.length };
  }

  /* series: [{name, color, values}] ; null values are drawn as a dash */
  function bars(box, labels, series, format = v => v) {
    const W = 420, H = 220, left = 46, bottom = 24, top = 14;
    const max = Math.max(1e-9, ...series.flatMap(s => s.values.filter(v => v !== null)));
    const root = svg('svg', { viewBox: `0 0 ${W} ${H}`, role: 'img' });
    const y = v => H - bottom - v / max * (H - bottom - top);
    for (const f of [0, 0.5, 1]) {
      svg('line', { x1: left, x2: W, y1: y(max * f), y2: y(max * f), class: f ? 'gridline' : 'axis' }, root);
      svg('text', { x: left - 5, y: y(max * f) + 4, 'text-anchor': 'end', class: 'tick' }, root).textContent = format(max * f);
    }
    const group = (W - left) / labels.length, width = Math.min(26, (group - 10) / series.length);
    labels.forEach((label, i) => {
      const start = left + group * i + (group - (width + 2) * series.length) / 2;
      series.forEach((s, j) => {
        const v = s.values[i], x = start + j * (width + 2);
        if (v === null) {
          svg('text', { x: x + width / 2, y: H - bottom - 4, class: 'value-label' }, root).textContent = '–';
          return;
        }
        const h = H - bottom - y(v), r = Math.min(4, h, width / 2);
        const bar = svg('path', {
          class: 'bar', fill: s.color,
          d: `M${x},${H - bottom}v${-(h - r)}q0,${-r} ${r},${-r}h${width - 2 * r}q${r},0 ${r},${r}v${h - r}z`,
        }, root);
        tip(bar, `Day ${label}${series.length > 1 ? ' · ' + s.name : ''}: ${format(v)}`);
      });
      svg('text', { x: left + group * i + group / 2, y: H - 8, 'text-anchor': 'middle', class: 'tick' }, root).textContent = 'Day ' + label;
    });
    box.replaceChildren(root);
  }

  /* Chosen rescue windows on one time axis (they never overlap). */
  function timeline(box, windows) {
    const W = 420, H = 66, end = Math.max(1440, ...windows.map(w => w[2]));
    const root = svg('svg', { viewBox: `0 0 ${W} ${H}`, role: 'img', 'aria-label': 'Rescue timetable' });
    const x = t => 8 + t / end * (W - 16);
    svg('line', { x1: x(0), x2: x(end), y1: 44, y2: 44, class: 'axis' }, root);
    for (const [id, start, finish, value] of windows) {
      const slot = svg('rect', { class: 'slot', x: x(start), y: 14, width: Math.max(1, x(finish) - x(start) - 1), height: 28, fill: '#1d1a15' }, root);
      tip(slot, `Window ${id}\nminute ${start} to ${finish}\nvalue ${value}`);
    }
    for (let h = 0; h <= end / 60; h += 6) {
      svg('text', { x: x(h * 60), y: 60, 'text-anchor': h ? 'middle' : 'start', class: 'tick' }, root).textContent = h + 'h';
    }
    box.replaceChildren(root);
  }

  return { map, bars, timeline, tip };
})();
