/* qmstrace's viewer only arranges precomputed evidence; it never judges or traverses. */
(() => {
  "use strict";
  const data = JSON.parse(document.getElementById("assessment").textContent);
  const $ = (id) => document.getElementById(id);
  const element = (tag, text, cls) => {
    const node = document.createElement(tag);
    if (text !== undefined) node.textContent = text;
    if (cls) node.className = cls;
    return node;
  };
  const colors = [
    "#d8e8d2",
    "#a9d8cb",
    "#b6d3eb",
    "#d5c7e8",
    "#eed8ac",
    "#e4c5c0",
  ];
  const typeSet = new Set(data.types);
  const markerNames = [...new Set(data.links.map((e) => e.marker))].sort();
  const markerSet = new Set(markerNames);
  let selected = data.nodes.findIndex((n) => n.id === data.selected);
  const network = new vis.Network(
    $("network"),
    { nodes: [], edges: [] },
    {
      physics: false,
      layout: { randomSeed: 1 },
      interaction: { hover: false, multiselect: false },
      nodes: {
        shape: "box",
        margin: 10,
        font: { size: 16, face: "system-ui" },
        widthConstraint: { maximum: 170 },
      },
      edges: {
        arrows: "to",
        smooth: {
          enabled: true,
          type: "cubicBezier",
          forceDirection: "horizontal",
          roundness: 0.3,
        },
        font: { size: 12, align: "middle" },
      },
    },
  );
  $("summary").textContent =
    `${data.project} · ${data.nodes.length} visible-to-run items · ${data.links.length} authored links · ${data.findings.length} findings`;
  for (const notice of data.evidence)
    $("evidence").append(element("p", notice));
  // Unverified evidence is visible even when its disclosure is collapsed.
  const limits = data.evidence.filter((t) =>
    /NOT |not pinned|not verified|lightweight|refused/i.test(t),
  );
  for (const notice of limits)
    $("evidence").parentElement.before(element("p", notice));
  data.types.forEach((type, i) => {
    const chip = element("span", type.replaceAll("_", " "), "chip");
    chip.style.background = colors[i % colors.length];
    $("legend").append(chip);
  });
  function filters(container, values, active) {
    for (const value of values) {
      const label = element("label");
      const box = element("input");
      box.type = "checkbox";
      box.checked = true;
      box.addEventListener("change", () => {
        box.checked ? active.add(value) : active.delete(value);
        draw();
      });
      label.append(box, document.createTextNode(value));
      $(container).append(label);
    }
  }
  filters("types", data.types, typeSet);
  filters("markers", markerNames, markerSet);
  function reach() {
    const result = new Set(selected < 0 ? [] : [selected]);
    if (selected < 0) return result;
    for (const direction of ["forward", "backward"]) {
      if ($("direction").value !== "both" && $("direction").value !== direction)
        continue;
      for (const [i, distance] of data.reach[selected][direction])
        if (distance <= Number($("depth").value)) result.add(i);
    }
    return result;
  }
  function draw() {
    const highlighted = reach(),
      visible = new Set(),
      rows = new Map();
    const nodes = [];
    data.nodes.forEach((n, i) => {
      if (
        !typeSet.has(n.type) ||
        ($("scope").value === "thread" && selected >= 0 && !highlighted.has(i))
      )
        return;
      visible.add(i);
      const row = rows.get(n.column) || 0;
      rows.set(n.column, row + 1);
      const label = n.id.length > 30 ? n.id.slice(0, 27) + "…" : n.id;
      nodes.push({
        id: i,
        // Supply a text-only element so authored titles never become tooltip markup.
        title: element("span", n.title || n.id),
        label:
          label + (n.badges.length ? "\n[" + n.badges.join(" · ") + "]" : ""),
        x: n.column * 230,
        y: row * 105,
        color: {
          background: colors[n.column % colors.length],
          border: i === selected ? "#006a65" : "#748880",
        },
        borderWidth: i === selected ? 4 : highlighted.has(i) ? 2 : 1,
        opacity: selected >= 0 && !highlighted.has(i) ? 0.35 : 1,
      });
    });
    const edges = data.links.flatMap((e, i) =>
      visible.has(e.src) && visible.has(e.dst) && markerSet.has(e.marker)
        ? [
            {
              id: i,
              from: e.src,
              to: e.dst,
              label: e.marker,
              dashes: e.dependency,
              color: {
                color: "#718d88",
                opacity:
                  selected >= 0 &&
                  !(highlighted.has(e.src) && highlighted.has(e.dst))
                    ? 0.12
                    : 0.7,
              },
            },
          ]
        : [],
    );
    network.setData({ nodes, edges });
    $("counts").textContent =
      `${visible.size} shown · ${data.nodes.length - visible.size} hidden items · ${edges.length} shown / ${data.links.length} links`;
  }
  function field(key, value) {
    const dl = element("dl");
    dl.append(element("dt", key), element("dd", value || "—"));
    $("inspector").append(dl);
  }
  function showFinding(f) {
    $("inspector").append(
      element("h3", f.code),
      element("p", f.where, "muted"),
      element("p", f.what),
      element("p", f.next),
    );
  }
  function select(i, focus = false) {
    selected = i;
    const n = data.nodes[i];
    typeSet.add(n.type);
    [...$("types").querySelectorAll("label")].forEach((label) => {
      if (label.textContent === n.type) label.firstChild.checked = true;
    });
    $("scope").value = "thread";
    $("inspector").replaceChildren(element("h3", n.id), element("p", n.title));
    field(
      "Type / ownership",
      `${n.type} · ${n.home}${n.repo ? " · " + n.repo : ""}`,
    );
    field("Source", n.where);
    field("State", n.badges.join(" · ") || "No baseline or suspect badge");
    if (n.baseline) field("Governing baseline", n.baseline);
    for (const [key, value] of Object.entries(n.fields)) field(key, value);
    for (const e of data.links.filter((e) => e.src === i || e.dst === i)) {
      const button = element(
        "button",
        `${data.nodes[e.src].id} — ${e.marker} → ${data.nodes[e.dst].id}`,
      );
      button.addEventListener("click", () => inspectLink(e));
      $("inspector").append(button);
    }
    data.findings.filter((f) => f.item === n.id).forEach(showFinding);
    draw();
    list();
    network.fit({ animation: false });
    if (focus) {
      $("inspector").tabIndex = -1;
      $("inspector").focus();
    }
  }
  function inspectLink(e) {
    $("inspector").replaceChildren(element("h3", "Authored relationship"));
    field("From", data.nodes[e.src].id);
    field("Marker", e.marker);
    field("To", data.nodes[e.dst].id);
    field("Declared at", e.where);
    field(
      "Coverage",
      e.dependency
        ? "Dependency only; counts toward no coverage"
        : "Ordinary link; configured coverage rules apply",
    );
  }
  function list() {
    const query = $("search").value.trim().toLowerCase();
    const matches = data.nodes
      .map((n, i) => [n, i])
      .filter(([n]) => (n.id + " " + n.title).toLowerCase().includes(query));
    $("items").replaceChildren();
    $("matches").textContent = `${matches.length} matching items`;
    for (const [n, i] of matches) {
      const b = element(
        "button",
        n.id +
          (n.title ? " · " + n.title : "") +
          (n.badges.length ? " [" + n.badges.join(" · ") + "]" : ""),
      );
      b.setAttribute("aria-pressed", String(i === selected));
      b.addEventListener("click", () => select(i, true));
      $("items").append(b);
    }
  }
  function findingList() {
    $("findings").replaceChildren();
    const found = data.findings.filter(
      (f) =>
        $("finding-kind").value === "all" ||
        f.code.startsWith($("finding-kind").value),
    );
    $("finding-title").textContent =
      `Findings · ${found.length} shown / ${data.findings.length} total`;
    for (const f of found) {
      const b = element("button", `${f.code} · ${f.what} ${f.next}`);
      b.addEventListener("click", () => {
        const i = data.nodes.findIndex((n) => n.id === f.item);
        if (i >= 0) select(i);
        else $("inspector").replaceChildren();
        if (
          i < 0 ||
          !data.findings.some((x) => x === f && x.item === data.nodes[i].id)
        )
          showFinding(f);
        $("inspector").tabIndex = -1;
        $("inspector").focus();
      });
      $("findings").append(b);
    }
    if (!found.length)
      $("findings").append(
        element(
          "p",
          "No findings in this selection. Source and evidence limits still apply.",
        ),
      );
  }
  network.on("click", (event) => {
    if (event.nodes.length) select(event.nodes[0]);
    else if (event.edges.length) inspectLink(data.links[event.edges[0]]);
  });
  $("search").addEventListener("input", list);
  $("finding-kind").addEventListener("change", findingList);
  for (const id of ["scope", "direction", "depth"])
    $(id).addEventListener("change", () => {
      draw();
      network.fit({ animation: false });
    });
  $("zoom-in").addEventListener("click", () =>
    network.moveTo({ scale: network.getScale() * 1.4 }),
  );
  $("zoom-out").addEventListener("click", () =>
    network.moveTo({ scale: network.getScale() / 1.4 }),
  );
  $("fit").addEventListener("click", () => network.fit({ animation: false }));
  $("reset").addEventListener("click", () => {
    selected = -1;
    $("scope").value = "all";
    $("direction").value = "both";
    $("depth").value = "999999";
    $("search").value = "";
    data.types.forEach((t) => typeSet.add(t));
    markerNames.forEach((t) => markerSet.add(t));
    document.querySelectorAll(".filters input").forEach((b) => {
      b.checked = true;
    });
    $("inspector").replaceChildren(
      element("p", "Select an item, link or finding."),
    );
    draw();
    list();
    network.fit({ animation: false });
  });
  list();
  findingList();
  if (selected >= 0) select(selected);
  else {
    draw();
    network.fit({ animation: false });
  }
})();
