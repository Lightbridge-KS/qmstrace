/* DOM contract tests for display-only controls; the real canvas is checked in browser replay. */
const { test } = require("node:test");
const assert = require("node:assert/strict");
const fs = require("node:fs");
const vm = require("node:vm");
const path = require("node:path");
class Element {
  constructor(tag = "div") {
    this.tag = tag;
    this.children = [];
    this.listeners = {};
    this.style = {};
    this.attributes = {};
    this.value = "";
    this.text = "";
    this.parentElement = null;
  }
  set textContent(value) {
    this.text = value;
    this.children = [];
  }
  get textContent() {
    return this.text + this.children.map((c) => c.textContent).join("");
  }
  get firstChild() {
    return this.children[0];
  }
  append(...children) {
    children.forEach((c) => {
      c.parentElement = this;
      this.children.push(c);
    });
  }
  before(...children) {
    this.parentElement?.append(...children);
  }
  replaceChildren(...children) {
    this.text = "";
    this.children = [];
    this.append(...children);
  }
  addEventListener(name, action) {
    this.listeners[name] = action;
  }
  setAttribute(key, value) {
    this.attributes[key] = value;
  }
  focus() {
    this.focused = true;
  }
  querySelectorAll(tag) {
    return this.children.flatMap((c) => [
      ...(c.tag === tag ? [c] : []),
      ...c.querySelectorAll(tag),
    ]);
  }
}
function mount() {
  const ids = {};
  for (const id of [
    "assessment",
    "network",
    "summary",
    "evidence",
    "legend",
    "types",
    "markers",
    "scope",
    "direction",
    "depth",
    "counts",
    "inspector",
    "items",
    "search",
    "matches",
    "findings",
    "finding-kind",
    "finding-title",
    "fit",
    "reset",
    "zoom-in",
    "zoom-out",
  ])
    ids[id] = new Element();
  ids.evidence.parentElement = new Element();
  ids.evidence.parentElement.parentElement = new Element();
  ids.scope.value = "all";
  ids.direction.value = "both";
  ids.depth.value = "999999";
  ids["finding-kind"].value = "all";
  const node = (id, type, column, title = "") => ({
    id,
    type,
    column,
    title,
    home: "this repo",
    fields: {},
    badges: [],
  });
  const payload = {
    project: "Fixture",
    selected: null,
    types: ["requirement", "design"],
    evidence: ["NOT VERIFIED: boundary"],
    nodes: [
      node("R", "requirement", 0, "<img onerror=attack()>"),
      node("D", "design", 1),
      node("H", "design", 1),
    ],
    links: [
      {
        src: 1,
        dst: 0,
        marker: "Satisfies",
        where: "design.md:2",
        dependency: false,
      },
    ],
    reach: [
      { forward: [[1, 1]], backward: [] },
      { forward: [], backward: [[0, 1]] },
      { forward: [], backward: [] },
    ],
    findings: [
      {
        code: "S01",
        item: "H",
        where: "history.md:1",
        what: "historical-only: root OLD; distance 1",
        next: "Review it.",
      },
      {
        code: "V13",
        item: "OLD",
        where: "old.md:1",
        what: "Removed",
        next: "Restore or withdraw.",
      },
    ],
  };
  ids.assessment.textContent = JSON.stringify(payload);
  let network;
  class Network {
    constructor() {
      network = this;
    }
    setData(value) {
      this.data = value;
    }
    fit() {}
    on(name, fn) {
      this[name] = fn;
    }
  }
  const document = {
    getElementById: (id) => ids[id],
    createElement: (tag) => new Element(tag),
    createTextNode: (text) => {
      const e = new Element();
      e.textContent = text;
      return e;
    },
    querySelectorAll: () => [
      ...ids.types.querySelectorAll("input"),
      ...ids.markers.querySelectorAll("input"),
    ],
  };
  vm.runInNewContext(
    fs.readFileSync(
      path.resolve(__dirname, "../../src/qmstrace/assets/graph.js"),
      "utf8",
    ),
    { document, vis: { Network } },
  );
  return { ids, network, payload };
}
test("selection uses supplied reach, filters do not remove findings, reset restores counts", () => {
  const { ids, network } = mount();
  assert.equal(network.data.nodes.length, 3);
  ids.items.children[0].listeners.click();
  assert.equal(ids.scope.value, "thread");
  assert.equal(network.data.nodes.length, 2);
  assert.match(ids.inspector.textContent, /<img onerror=attack\(\)>/);
  assert.equal(ids.inspector.querySelectorAll("img").length, 0);
  assert.equal(ids.findings.children.length, 2);
  const box = ids.markers.children[0].firstChild;
  box.checked = false;
  box.listeners.change();
  assert.equal(network.data.edges.length, 0);
  assert.equal(network.data.nodes.length, 2);
  assert.match(ids.counts.textContent, /1 hidden/);
  ids.reset.listeners.click();
  assert.equal(network.data.nodes.length, 3);
  assert.equal(network.data.edges.length, 1);
});
test("historical-only and deleted-item findings remain inspectable", () => {
  const { ids, network } = mount();
  ids.findings.children[0].listeners.click();
  assert.match(ids.inspector.textContent, /historical-only: root OLD/);
  assert.deepEqual(
    Array.from(network.data.nodes, (n) => n.id),
    [2],
  );
  ids.findings.children[1].listeners.click();
  assert.match(ids.inspector.textContent, /V13.*RemovedRestore or withdraw/s);
  ids["finding-kind"].value = "S";
  ids["finding-kind"].listeners.change();
  assert.equal(ids.findings.children.length, 1);
});
test("search remains global; depth and direction select only supplied reach", () => {
  const { ids, network } = mount();
  ids.items.children[1].listeners.click();
  ids.direction.value = "forward";
  ids.direction.listeners.change();
  assert.deepEqual(
    Array.from(network.data.nodes, (n) => n.id),
    [1],
  );
  ids.search.value = "H";
  ids.search.listeners.input();
  assert.equal(ids.items.children.length, 1);
  ids.items.children[0].listeners.click();
  assert.match(ids.inspector.textContent, /historical-only/);
});

test("node tooltips preserve literal titles and fall back to full IDs", () => {
  const { ids, network, payload } = mount();
  const assertTitles = () => {
    for (const node of network.data.nodes) {
      const source = payload.nodes[node.id];
      assert.equal(node.title.textContent, source.title || source.id);
      assert.equal(node.title.querySelectorAll("img").length, 0);
      assert.equal(node.title.children.length, 0);
    }
  };
  assertTitles(); // Includes a hostile HTML-looking title and untitled nodes.
  ids.items.children[0].listeners.click();
  assertTitles();
  ids.reset.listeners.click();
  assertTitles();
});
