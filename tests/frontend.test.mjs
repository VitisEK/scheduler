import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import test from "node:test";
import { JSDOM } from "jsdom";

const source = (await readFile(new URL("../custom_components/profile_scheduler/frontend/panel.js", import.meta.url), "utf8"))
  .replace("export class ProfileSchedulerPanel", "class ProfileSchedulerPanel");

async function setup({ editors = true, document = { enabled: false, topics: [] } } = {}) {
  const dom = new JSDOM("<!doctype html><body></body>", { url: "http://ha.test/profile-scheduler", runScripts: "outside-only" });
  const { window } = dom;
  const confirmations = [];
  if (editors) {
    for (const tag of ["ha-form", "ha-selector", "ha-dialog", "ha-button"]) window.customElements.define(tag, class extends window.HTMLElement {});
    window.loadCardHelpers = async () => ({ showConfirmationDialog: async (_host, params) => { confirmations.push(params); return true; } });
  }
  window.eval(source);
  let stored = structuredClone(document);
  let revision = 0;
  const calls = [];
  const panel = window.document.createElement("profile-scheduler-panel");
  const snapshot = () => ({ document: structuredClone(stored), revision, next_change: null, last_error: null });
  panel.hass = {
    language: "cs", config: { time_zone: "Europe/Prague" }, states: { "climate.office": { attributes: { friendly_name: "Pracovna" } } },
    callWS: async (message) => {
      calls.push(structuredClone(message));
      if (message.type.endsWith("/save")) {
        assert.equal(message.revision, revision);
        stored = structuredClone(message.document); revision++;
      } else if (message.type.endsWith("/set_profile")) { stored.topics.find((topic) => topic.id === message.topic_id).active_profile = message.profile_id; revision++; }
      else if (message.type.endsWith("/set_enabled")) { stored.enabled = message.enabled; revision++; }
      return snapshot();
    },
  };
  window.document.body.append(panel);
  await new Promise((resolve) => window.setTimeout(resolve, 0));
  return { dom, window, panel, calls, confirmations, read: () => stored };
}
function change(window, form, value) {
  form.dispatchEvent(new window.CustomEvent("value-changed", { detail: { value }, bubbles: true, composed: true }));
}
async function click(window, root, text) {
  const button = [...root.querySelectorAll("ha-button")].find((item) => item.textContent === text);
  assert.ok(button, `Button ${text} exists`);
  button.click();
  await new Promise((resolve) => window.setTimeout(resolve, 0));
}

const tick = (window) => new Promise((resolve) => window.setTimeout(resolve, 0));
const plain = (value) => JSON.parse(JSON.stringify(value));
async function edit(window, panel, button, value) {
  await click(window, panel.shadowRoot, button);
  const dialog = panel.shadowRoot.querySelector("ha-dialog");
  change(window, dialog.querySelector("ha-form"), value);
  await click(window, dialog, "Uložit");
}

test("topic entities, profiles, native editors and independent activation", async () => {
  const app = await setup();
  const { window, panel, calls } = app;
  try {
    Object.defineProperty(window.crypto, "randomUUID", { value: undefined });
    await edit(window, panel, "Přidat téma", { name: "Topení" });
    await click(window, panel.shadowRoot, "Přidat řádek");
    let dialog = panel.shadowRoot.querySelector("ha-dialog");
    assert.deepEqual(plain(dialog.querySelector("ha-form").schema[1].selector), { entity: { multiple: true } });
    change(window, dialog.querySelector("ha-form"), { name: "Pracovna", entity_ids: ["climate.office"] });
    await click(window, dialog, "Uložit");
    await edit(window, panel, "Přidat profil", { name: "Doma", schedule_mode: "daily" });
    await click(window, panel.shadowRoot, "Přidat úsek");
    dialog = panel.shadowRoot.querySelector("ha-dialog");
    const form = dialog.querySelector("ha-form");
    change(window, form, { label: "21 °C", start: "06:00", end: "22:00", mode: "state", color: "#1976d2" });
    const actions = dialog.querySelector("ha-selector");
    assert.deepEqual(plain(actions.selector), { action: { optionsInSidebar: false } });
    change(window, actions, [{ action: "climate.set_temperature", target: {}, data: { temperature: 21 } }]);
    assert.equal(actions.value[0].target.entity_id[0], "climate.office");
    change(window, actions, [...actions.value, { action: "climate.turn_on" }]);
    change(window, form, { ...form.data, label: "21 °C", start: "06:00", end: "23:00", mode: "state", color: "#1976d2", actions: [] });
    app.panel.hass = { ...app.panel.hass, states: {} };
    assert.equal(panel.shadowRoot.querySelector("ha-dialog"), dialog);
    await click(window, dialog, "Uložit");
    await click(window, panel.shadowRoot, "Uložit");
    const saved = app.read().topics[0];
    assert.equal(saved.profiles[0].schedules.all[0].id, saved.entities[0].id);
    assert.equal(saved.profiles[0].schedules.all[0].blocks[0].end, "23:00");
    assert.equal(saved.profiles[0].schedules.all[0].blocks[0].actions.length, 2);
    assert.deepEqual(saved.profiles[0].schedules.all[0].blocks[0].actions[0].target, { entity_id: ["climate.office"] });
    change(window, panel.shadowRoot.querySelector("ha-form"), { active: saved.profiles[0].id });
    await tick(window);
    assert.deepEqual(calls.find((call) => call.type.endsWith("/set_profile")), { type: "profile_scheduler/set_profile", topic_id: saved.id, profile_id: saved.profiles[0].id });
    await edit(window, panel, "Přidat téma", { name: "Světla" });
    await edit(window, panel, "Přidat profil", { name: "Večer", schedule_mode: "daily" });
    await click(window, panel.shadowRoot, "Uložit");
    const second = app.read().topics[1];
    change(window, panel.shadowRoot.querySelector("ha-form"), { active: second.profiles[0].id });
    await tick(window);
    assert.equal(app.read().topics[0].active_profile, saved.profiles[0].id);
    assert.equal(app.read().topics[1].active_profile, second.profiles[0].id);
    change(window, panel.shadowRoot.querySelector("ha-form"), { active: "__none__" });
    await tick(window);
    assert.equal(app.read().topics[1].active_profile, null);
    await click(window, panel.shadowRoot, "Zapnout");
    assert.equal(app.read().enabled, true);
  } finally { panel.remove(); app.dom.window.close(); }
});

test("weekly days and profiles stay isolated; deleting an entity cleans all schedules", async () => {
  const block = { id: "b", label: "Heat", start: "06:00", end: "07:00", mode: "state", color: "#1976d2", actions: [{ action: "climate.turn_on" }] };
  const document = { enabled: true, topics: [{ id: "t", name: "Topic", active_profile: "p", entities: [{ id: "e", name: "Room", entity_ids: ["climate.office"] }], profiles: [
    { id: "p", name: "Weekly", schedule_mode: "weekly", schedules: { "0": [{ id: "e", blocks: [block] }], "1": [] } },
    { id: "q", name: "Daily", schedule_mode: "daily", schedules: { all: [{ id: "e", blocks: [block] }] } },
  ] }] };
  const app = await setup({ document });
  const { window, panel } = app;
  try {
    assert.match(panel.shadowRoot.querySelector(".block").textContent, /Heat/);
    let day = [...panel.shadowRoot.querySelectorAll("ha-form")].find((form) => form.schema[0].name === "day");
    change(window, day, { day: "1" });
    assert.equal(panel.shadowRoot.querySelector(".block"), null);
    await click(window, panel.shadowRoot, "Přidat úsek");
    let dialog = panel.shadowRoot.querySelector("ha-dialog");
    change(window, dialog.querySelector("ha-form"), { label: "Tuesday", start: "09:00", end: "10:00", mode: "once", color: "#1976d2" });
    change(window, dialog.querySelector("ha-selector"), [{ action: "climate.turn_on" }]);
    await click(window, dialog, "Uložit");
    day = [...panel.shadowRoot.querySelectorAll("ha-form")].find((form) => form.schema[0].name === "day");
    change(window, day, { day: "0" });
    assert.match(panel.shadowRoot.querySelector(".block").textContent, /Heat/);
    await click(window, panel.shadowRoot, "Uložit");
    let profiles = app.read().topics[0].profiles;
    assert.equal(profiles[0].schedules["1"][0].blocks[0].label, "Tuesday");
    assert.equal(profiles[1].schedules.all[0].blocks[0].label, "Heat");
    await click(window, panel.shadowRoot, "Upravit řádek");
    dialog = panel.shadowRoot.querySelector("ha-dialog");
    await click(window, dialog, "Smazat");
    await click(window, panel.shadowRoot, "Uložit");
    profiles = app.read().topics[0].profiles;
    assert.equal(app.read().topics[0].entities.length, 0);
    assert.deepEqual(profiles[0].schedules["0"], []);
    assert.deepEqual(profiles[0].schedules["1"], []);
    assert.deepEqual(profiles[1].schedules.all, []);
  } finally { panel.remove(); app.dom.window.close(); }
});

test("editing row entities updates only matching direct targets across profiles and days", async () => {
  const actions = [
    { action: "climate.turn_on", target: { entity_id: "climate.office" } },
    { service: "climate.turn_on", data: { entity_id: ["climate.office"], temperature: 21 } },
    { action: "climate.turn_on", target: { entity_id: ["climate.office", "climate.other"] } },
    { action: "climate.turn_on", target: { area_id: "office", entity_id: "climate.office" } },
    { action: "climate.turn_on", target: { entity_id: "climate.other" } },
    { if: [], then: [{ action: "climate.turn_on", target: { entity_id: "climate.office" } }] },
  ];
  const block = { id: "b", label: "Heat", start: "06:00", end: "07:00", mode: "state", color: "#1976d2", actions };
  const row = (id) => ({ id, blocks: [structuredClone(block)] });
  const document = { enabled: false, topics: [{ id: "t", name: "Topic", active_profile: null, entities: [
    { id: "e", name: "Room", entity_ids: ["climate.office"] }, { id: "other", name: "Other", entity_ids: ["climate.office"] },
  ], profiles: [
    { id: "p", name: "Weekly", schedule_mode: "weekly", schedules: { "0": [row("e"), row("other")], "1": [row("e")] } },
    { id: "q", name: "Daily", schedule_mode: "daily", schedules: { all: [row("e")] } },
  ] }] };
  const app = await setup({ document });
  const { window, panel } = app;
  try {
    await click(window, panel.shadowRoot, "Upravit řádek");
    let dialog = panel.shadowRoot.querySelector("ha-dialog");
    change(window, dialog.querySelector("ha-form"), { name: "Room", entity_ids: [] });
    await click(window, dialog, "Uložit");
    assert.match(dialog.querySelector(".error").textContent, /časovými úseky/);
    assert.deepEqual(plain(panel._document), document);
    change(window, dialog.querySelector("ha-form"), { name: "Room", entity_ids: ["climate.new", "climate.second"] });
    await click(window, dialog, "Uložit");
    await click(window, panel.shadowRoot, "Uložit");
    const topic = app.read().topics[0];
    assert.deepEqual(topic.entities[0].entity_ids, ["climate.new", "climate.second"]);
    for (const entry of [topic.profiles[0].schedules["0"][0], topic.profiles[0].schedules["1"][0], topic.profiles[1].schedules.all[0]]) {
      const updated = entry.blocks[0].actions;
      assert.deepEqual(updated[0].target.entity_id, ["climate.new", "climate.second"]);
      assert.deepEqual(updated[1].data, { entity_id: ["climate.new", "climate.second"], temperature: 21 });
      assert.deepEqual(updated.slice(2), actions.slice(2));
    }
    assert.deepEqual(topic.profiles[0].schedules["0"][1].blocks[0].actions, actions);
    await click(window, panel.shadowRoot, "Upravit řádek");
    dialog = panel.shadowRoot.querySelector("ha-dialog");
    change(window, dialog.querySelector("ha-form"), { name: "Room", entity_ids: ["climate.final"] });
    await click(window, dialog, "Uložit");
    await click(window, panel.shadowRoot, "Uložit");
    assert.deepEqual(app.read().topics[0].profiles[1].schedules.all[0].blocks[0].actions[0].target.entity_id, ["climate.final"]);
  } finally { panel.remove(); app.dom.window.close(); }
});

test("mode conversion copies selected schedule after confirmation", async () => {
  const document = { enabled: false, topics: [{ id: "t", name: "T", entities: [], active_profile: null, profiles: [{ id: "p", name: "P", schedule_mode: "daily", schedules: { all: [] } }] }] };
  const app = await setup({ document });
  try {
    await edit(app.window, app.panel, "Upravit profil", { name: "P", schedule_mode: "weekly" });
    assert.equal(app.confirmations.length, 1);
    await click(app.window, app.panel.shadowRoot, "Uložit");
    assert.deepEqual(Object.keys(app.read().topics[0].profiles[0].schedules), ["0", "1", "2", "3", "4", "5", "6"]);
  } finally { app.panel.remove(); app.dom.window.close(); }
});

test("renaming and deleting topics and profiles updates only the selected topic", async () => {
  const document = { enabled: false, topics: [
    { id: "t1", name: "First", entities: [], active_profile: "p1", profiles: [{ id: "p1", name: "Old", schedule_mode: "daily", schedules: { all: [] } }] },
    { id: "t2", name: "Second", entities: [], active_profile: null, profiles: [] },
  ] };
  const app = await setup({ document });
  const { window, panel } = app;
  try {
    await edit(window, panel, "Upravit téma", { name: "Renamed" });
    await edit(window, panel, "Upravit profil", { name: "New", schedule_mode: "daily" });
    await click(window, panel.shadowRoot, "Uložit");
    assert.equal(app.read().topics[0].name, "Renamed");
    assert.equal(app.read().topics[0].profiles[0].name, "New");
    await click(window, panel.shadowRoot, "Upravit profil");
    await click(window, panel.shadowRoot.querySelector("ha-dialog"), "Smazat");
    await click(window, panel.shadowRoot, "Uložit");
    assert.equal(app.read().topics[0].active_profile, null);
    assert.deepEqual(app.read().topics[0].profiles, []);
    await click(window, panel.shadowRoot, "Upravit téma");
    await click(window, panel.shadowRoot.querySelector("ha-dialog"), "Smazat");
    await click(window, panel.shadowRoot, "Uložit");
    assert.deepEqual(app.read().topics.map((topic) => topic.id), ["t2"]);
  } finally { panel.remove(); app.dom.window.close(); }
});

test("cold panel explains native editor bootstrap", async () => {
  const app = await setup({ editors: false });
  try {
    assert.match(app.panel.shadowRoot.textContent, /standardních editorů/);
    assert.equal(app.panel.shadowRoot.querySelector("a").getAttribute("href"), "/lovelace/0");
    await click(app.window, app.panel.shadowRoot, "Přidat téma");
    assert.equal(app.panel.shadowRoot.querySelector("ha-dialog"), null);
  } finally { app.panel.remove(); app.dom.window.close(); }
});
