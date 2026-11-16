import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import test from "node:test";
import { JSDOM } from "jsdom";

const source = (await readFile(new URL("../custom_components/profile_scheduler/frontend/panel.js", import.meta.url), "utf8"))
  .replace("export class ProfileSchedulerPanel", "class ProfileSchedulerPanel");

async function setup({ editors = true } = {}) {
  const dom = new JSDOM("<!doctype html><body></body>", { url: "http://ha.test/profile-scheduler", runScripts: "outside-only" });
  const { window } = dom;
  const confirmations = [];
  if (editors) {
    for (const tag of ["ha-form", "ha-selector", "ha-dialog", "ha-button"]) window.customElements.define(tag, class extends window.HTMLElement {});
    window.loadCardHelpers = async () => ({ showConfirmationDialog: async (_host, params) => { confirmations.push(params); return true; } });
  }
  window.eval(source);
  let stored = { enabled: false, manual_profile: null, profiles: [] };
  let revision = 0;
  const calls = [];
  const panel = window.document.createElement("profile-scheduler-panel");
  const snapshot = () => ({ document: structuredClone(stored), revision, active_profile: stored.manual_profile, next_change: null, last_error: null });
  panel.hass = {
    language: "cs", config: { time_zone: "Europe/Prague" }, states: { "climate.office": { attributes: { friendly_name: "Pracovna" } } },
    callWS: async (message) => {
      calls.push(structuredClone(message));
      if (message.type.endsWith("/save")) {
        assert.equal(message.revision, revision);
        stored = structuredClone(message.document); revision++;
      } else if (message.type.endsWith("/set_profile")) { stored.manual_profile = message.profile_id; revision++; }
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

test("create profile → native entity/action selectors → time block → persist → activate", async () => {
  const app = await setup();
  const { window, panel, calls } = app;
  try {
    Object.defineProperty(window.crypto, "randomUUID", { value: undefined });
    await click(window, panel.shadowRoot, "Přidat profil");
    let dialog = panel.shadowRoot.querySelector("ha-dialog");
    change(window, dialog.querySelector("ha-form"), { name: "Doma", weekdays: ["0", "1"] });
    await click(window, dialog, "Uložit");
    await click(window, panel.shadowRoot, "Přidat řádek");
    dialog = panel.shadowRoot.querySelector("ha-dialog");
    const entityForm = dialog.querySelector("ha-form");
    assert.deepEqual(JSON.parse(JSON.stringify(entityForm.schema[1].selector)), { entity: { multiple: true } });
    change(window, entityForm, { name: "Pracovna", entity_ids: ["climate.office"] });
    await click(window, dialog, "Uložit");
    await click(window, panel.shadowRoot, "Přidat úsek");
    dialog = panel.shadowRoot.querySelector("ha-dialog");
    change(window, dialog.querySelector("ha-form"), { label: "21 °C", start: "06:00", end: "22:00", mode: "state", color: "#1976d2" });
    const actionSelector = dialog.querySelector("ha-selector");
    assert.deepEqual(JSON.parse(JSON.stringify(actionSelector.selector)), { action: { optionsInSidebar: false } });
    change(window, actionSelector, [{ action: "climate.set_temperature", target: {}, data: { temperature: 21 } }]);
    assert.equal(actionSelector.value[0].target.entity_id[0], "climate.office");
    change(window, actionSelector, [
      { action: "climate.set_temperature", target: { entity_id: ["climate.office"] }, data: { temperature: 21 } },
      { action: "climate.set_hvac_mode", target: { entity_id: ["climate.office"] }, data: { hvac_mode: "heat" } },
    ]);
    assert.equal(actionSelector.value.length, 2, "controlled native editor receives every sequence update");
    const timeForm = dialog.querySelector("ha-form");
    assert.equal("actions" in timeForm.data, false, "native time form does not retain a stale copy of action data");
    change(window, timeForm, { ...timeForm.data, label: "21 °C", start: "06:00", end: "23:00", mode: "state", color: "#1976d2", actions: [] });
    await click(window, dialog, "Uložit");
    assert.match(panel.shadowRoot.querySelector(".block").textContent, /21 °C/);
    await click(window, panel.shadowRoot, "Uložit");
    const save = calls.find((item) => item.type.endsWith("/save"));
    const block = save.document.profiles[0].rows[0].blocks[0];
    assert.deepEqual(block.actions[0].target, { entity_id: ["climate.office"] });
    assert.equal(block.start, "06:00");
    assert.equal(block.end, "23:00");
    assert.equal(block.actions.length, 2, "changing time after editing actions preserves the sequence");
    assert.deepEqual(save.document.profiles[0].weekdays, [0, 1]);
    const manual = panel.shadowRoot.querySelector("ha-form");
    change(window, manual, { manual: save.document.profiles[0].id });
    await new Promise((resolve) => window.setTimeout(resolve, 0));
    await click(window, panel.shadowRoot, "Zapnout");
    assert.equal(app.read().enabled, true);
    assert.equal(app.read().manual_profile, save.document.profiles[0].id);
  } finally { panel.remove(); app.dom.window.close(); }
});

test("cold panel explains native editor bootstrap instead of showing a broken action editor", async () => {
  const app = await setup({ editors: false });
  try {
    assert.match(app.panel.shadowRoot.textContent, /standardních editorů/);
    assert.equal(app.panel.shadowRoot.querySelector("a").getAttribute("href"), "/lovelace/0");
    await click(app.window, app.panel.shadowRoot, "Přidat profil");
    assert.equal(app.panel.shadowRoot.querySelector("ha-dialog"), null);
  } finally { app.panel.remove(); app.dom.window.close(); }
});

test("an HA state update preserves an in-progress native action editor", async () => {
  const app = await setup();
  try {
    await click(app.window, app.panel.shadowRoot, "Přidat profil");
    const dialog = app.panel.shadowRoot.querySelector("ha-dialog");
    app.panel.hass = { ...app.panel.hass, states: {} };
    assert.equal(app.panel.shadowRoot.querySelector("ha-dialog"), dialog);
  } finally { app.panel.remove(); app.dom.window.close(); }
});
