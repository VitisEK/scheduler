/* Native HA controls surround the only custom UI: the daily timeline. */
const TEXT = {
  cs: {
    sectionEntities: "Entity", sectionProfiles: "Profily", sectionPlan: "Plán", topics: "Témata", addTopic: "Přidat téma", editTopic: "Upravit téma", schedule_mode: "Režim plánu", daily: "Každý den", weekly: "Podle dne v týdnu", changeMode: "Změnit režim plánu? Stávající plány budou nahrazeny kopií vybraného dne.", day: "Den plánu", title: "Scheduler", profiles: "Profily", addProfile: "Přidat profil", editProfile: "Upravit profil",
    addRow: "Přidat řádek", editRow: "Upravit řádek", addBlock: "Přidat úsek", editBlock: "Upravit úsek",
    name: "Název", weekdays: "Dny pro automatický výběr", entities: "Výchozí cílové entity", entity_ids: "Entity",
    start: "Začátek (HH:MM)", end: "Konec (HH:MM nebo 24:00)", label: "Popisek úseku",
    mode: "Vykonávání", state: "Stav – obnovit také po restartu", once: "Jednorázově – pouze na začátku",
    color: "Barva", actions: "Akce Home Assistant", save: "Uložit", cancel: "Zrušit", remove: "Smazat",
    confirm: "Opravdu smazat?", enabled: "Plán je zapnutý", disabled: "Plán je vypnutý", enable: "Zapnout", disable: "Vypnout",
    active: "Aktivní profil", next: "Nejbližší změna", automatic: "Automaticky podle dnů", manual: "Ruční výběr profilu",
    noProfile: "Žádný profil", empty: "Vyberte nebo vytvořte profil a přidejte řádek s cílovými entitami.",
    noRows: "Přidejte první řádek a pak časové úseky. Kliknutí na prázdnou osu přidá půlhodinový úsek.",
    unsaved: "Neuložené změny", saved: "Uloženo", reload: "Znovu načíst", error: "Chyba",
    bootstrap: "Pro načtení standardních editorů otevřete přehled Home Assistantu a potom se vraťte do Scheduleru. Poté stiskněte Znovu načíst editory.",
    dashboard: "Otevřít přehled", retry: "Znovu načíst editory", unavailable: "Standardní editory HA nejsou dostupné. Zkontrolujte podporovanou verzi HA.",
    stateHelp: "Stavové úseky obnovují teplotu a jiné nastavené hodnoty. Scény, skripty a složité sekvence používejte jednorázově. Za koncem úseku zůstane poslední stav; pro vypnutí přidejte další úsek.",
    entityValues: "Hodnoty entit", temperature: "Teplota", on: "Zapnuto", off: "Vypnuto", value: "Hodnota",
    actionHelp: "Cíle a parametry upravte přímo v nativním editoru akcí. Cíle řádku se předvyplní pouze do první nově vytvořené akce.",
    overlap: "Časy musí mít formát HH:MM a úseky jednoho řádku se nesmějí překrývat.",
    chooseAction: "Přidejte alespoň jednu akci v editoru Home Assistantu.", conflict: "Plán se mezitím změnil. Neuložený návrh zůstal zde; zkopírujte jej nebo znovu načtěte aktuální plán.",
    discard: "Zahodit neuložené změny a načíst uložený plán?", blankName: "Vyplňte název nebo popisek.",
    clearRowTargets: "Řádek s časovými úseky musí mít cílové entity. Nejprve odstraňte jeho úseky ze všech profilů a dnů.",
    group: "Skupina akcí", timeAxis: "Denní časová osa od 00:00 do 24:00, krok 30 minut",
    colors: ["Modrá", "Zelená", "Oranžová", "Fialová", "Červená", "Tyrkysová"],
    days: ["Pondělí", "Úterý", "Středa", "Čtvrtek", "Pátek", "Sobota", "Neděle"],
  },
  en: {
    sectionEntities: "Entities", sectionProfiles: "Profiles", sectionPlan: "Schedule", topics: "Topics", addTopic: "Add topic", editTopic: "Edit topic", schedule_mode: "Schedule mode", daily: "Every day", weekly: "By weekday", changeMode: "Change schedule mode? Existing plans will be replaced with a copy of the selected day.", day: "Plan day", title: "Scheduler", profiles: "Profiles", addProfile: "Add profile", editProfile: "Edit profile",
    addRow: "Add row", editRow: "Edit row", addBlock: "Add time block", editBlock: "Edit time block",
    name: "Name", weekdays: "Days for automatic selection", entities: "Default target entities", entity_ids: "Entities",
    start: "Start (HH:MM)", end: "End (HH:MM or 24:00)", label: "Block label",
    mode: "Execution", state: "State – also restore on restart", once: "One shot – only at the start",
    color: "Color", actions: "Home Assistant actions", save: "Save", cancel: "Cancel", remove: "Delete",
    confirm: "Delete this item?", enabled: "Schedule is enabled", disabled: "Schedule is disabled", enable: "Enable", disable: "Disable",
    active: "Active profile", next: "Next change", automatic: "Automatic by weekday", manual: "Manual profile override",
    noProfile: "No profile", empty: "Select or create a profile, then add a row with target entities.",
    noRows: "Add your first row, then time blocks. Click an empty timeline to add a 30-minute block.",
    unsaved: "Unsaved changes", saved: "Saved", reload: "Reload", error: "Error",
    bootstrap: "To load the standard editors, open the Home Assistant dashboard, return to Scheduler, then press Reload editors.",
    dashboard: "Open dashboard", retry: "Reload editors", unavailable: "Standard HA editors are unavailable. Check the supported HA version.",
    stateHelp: "State blocks restore temperature and other set values. Use one-shot mode for scenes, scripts and complex sequences. The last state remains after a block ends; add another block to turn a device off.",
    entityValues: "Entity values", temperature: "Temperature", on: "On", off: "Off", value: "Value",
    actionHelp: "Edit targets and parameters in the native action editor. Row targets prefill only the first newly created action.",
    overlap: "Use HH:MM times; blocks in the same row must not overlap.",
    chooseAction: "Add at least one action in the Home Assistant editor.", conflict: "The schedule changed elsewhere. Your draft is still here; copy it or reload the current schedule.",
    discard: "Discard unsaved changes and reload the saved schedule?", blankName: "Enter a name or label.",
    clearRowTargets: "A row with time blocks must have target entities. First remove its blocks from every profile and day.",
    group: "Action group", timeAxis: "Daily timeline from 00:00 to 24:00 in 30-minute steps",
    colors: ["Blue", "Green", "Orange", "Purple", "Red", "Teal"],
    days: ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"],
  },
};
const COLORS = ["#1976d2", "#287d3c", "#a94f00", "#8050ad", "#bc3039", "#007b83"];
const clone = (value) => JSON.parse(JSON.stringify(value));
// getRandomValues is also available on local HTTP installations of HA, where
// the secure-context-only randomUUID API may be absent.
const newId = () => crypto.randomUUID?.() || Array.from(crypto.getRandomValues(new Uint8Array(16)), (value) => value.toString(16).padStart(2, "0")).join("");
const minutes = (time) => Number(time.slice(0, 2)) * 60 + Number(time.slice(3));
const clock = (value) => `${String(Math.floor(value / 60)).padStart(2, "0")}:${String(value % 60).padStart(2, "0")}`;
const el = (tag, text, className) => {
  const node = document.createElement(tag);
  if (text !== undefined) node.textContent = text;
  if (className) node.className = className;
  return node;
};

// Use the entity metadata supplied by HA, and generate ordinary HA actions so
// saved plans can still be edited in the native action editor.
const POWER_DOMAINS = new Set(["switch", "input_boolean", "light", "fan"]);

function valueControl(entityId, hass, translate) {
  const domain = entityId.split(".")[0];
  const attributes = hass.states[entityId]?.attributes;
  if (!attributes) return undefined;
  if (POWER_DOMAINS.has(domain)) {
    const options = ["on", "off"].map((value) => ({ value, label: translate(value) }));
    return { label: translate("value"), selector: { select: { options } }, options, domain };
  }
  if (["select", "input_select"].includes(domain)) {
    if (!Array.isArray(attributes.options) || !attributes.options.length) return undefined;
    const options = attributes.options.map((value) => ({ value, label: value }));
    return { label: translate("value"), selector: { select: { options } },
      options, service: domain + ".select_option", field: "option" };
  }

  const climate = domain === "climate";
  // ClimateEntityFeature.TARGET_TEMPERATURE in HA.
  if (climate && !(attributes.supported_features & 1)) return undefined;
  if (!climate && !["number", "input_number"].includes(domain)) return undefined;
  const { min, max, step, unit_of_measurement: unit } = climate
    ? { min: attributes.min_temp, max: attributes.max_temp, step: attributes.target_temp_step, unit_of_measurement: hass.config.unit_system?.temperature }
    : attributes;
  if (!Number.isFinite(min) || !Number.isFinite(max) || max < min) return undefined;
  const number = { min, max, step: step > 0 ? step : "any", mode: "box" };
  if (unit) number.unit_of_measurement = unit;
  return { label: translate(climate ? "temperature" : "value"), selector: { number },
    service: climate ? "climate.set_temperature" : domain + ".set_value",
    field: climate ? "temperature" : "value", unit };
}

function readSimpleValue(action, entityId, control) {
  if (Object.keys(action).some((key) => !["action", "service", "target", "data"].includes(key))) return undefined;
  const target = action.target;
  if (!target || Object.keys(target).length !== 1) return undefined;
  const ids = Array.isArray(target.entity_id) ? target.entity_id : [target.entity_id];
  if (ids.length !== 1 || ids[0] !== entityId) return undefined;
  const service = action.action || action.service;
  const data = action.data || {};
  if (control.field) {
    if (service === control.service && Object.keys(data).length === 1) return data[control.field];
  } else if (!Object.keys(data).length) {
    return ["on", "off"].find((value) => service === control.domain + ".turn_" + value);
  }
  return undefined;
}

export class ProfileSchedulerPanel extends HTMLElement {
  constructor() {
    super();
    this.attachShadow({ mode: "open" });
    this._dirty = false;
    this._busy = false;
    this._editors = false;
    this._error = "";
    this._onUnload = (event) => { if (this._dirty) { event.preventDefault(); event.returnValue = ""; } };
  }

  set hass(value) {
    this._hass = value;
    if (!this.isConnected) return;
    // Preserve an open native editor, focus and draft across HA state updates.
    for (const node of this.shadowRoot.querySelectorAll("ha-form, ha-selector")) node.hass = value;
    if (this._dialog) for (const node of this._dialog.querySelectorAll("ha-form, ha-selector")) node.hass = value;
    if (!this._loaded && !this._loading) void this._load();
  }
  get hass() { return this._hass; }
  set narrow(value) { this._narrow = value; }

  connectedCallback() {
    window.addEventListener("beforeunload", this._onUnload);
    if (this.hass && !this._loaded) void this._load();
    this._timer = window.setInterval(() => {
      if (this._loaded && !this._dirty && !this._dialog && !this._busy) void this._refreshStatus();
    }, 30000);
  }
  disconnectedCallback() {
    clearInterval(this._timer);
    window.removeEventListener("beforeunload", this._onUnload);
    this._dialog?.remove();
    this._dialog = undefined;
  }
  _t(key) { return (TEXT[this.hass?.language?.startsWith("cs") ? "cs" : "en"])[key]; }
  _button(label, action, secondary = false) {
    const button = el("ha-button", label);
    if (secondary) button.setAttribute("appearance", "plain");
    button.disabled = this._busy;
    button.addEventListener("click", async () => {
      button.disabled = true;
      try { await action(); }
      catch (err) {
        if (this._dialog) this._dialog.querySelector(".error").textContent = err.message || String(err);
        else { this._error = err.message || String(err); this._render(); }
      } finally { button.disabled = this._busy; }
    });
    return button;
  }
  async _nativeEditors() {
    if (!customElements.get("ha-form") || !customElements.get("ha-selector")) {
      if (!window.loadCardHelpers) return false;
      const helpers = await window.loadCardHelpers();
      const card = helpers.createCardElement({ type: "button" });
      await card.constructor.getConfigElement();
    }
    if (window.loadCardHelpers) this._helpers = await window.loadCardHelpers();
    this._editors = !!customElements.get("ha-form") && !!customElements.get("ha-selector") && !!this._helpers;
    return this._editors;
  }
  async _load() {
    this._loading = true;
    try {
      const result = await this.hass.callWS({ type: "profile_scheduler/get" });
      this._document = clone(result.document);
      this._status = result;
      this._revision = result.revision;
      this._syncSelection();
      this._dirty = false;
      this._error = "";
      this._loaded = true;
      await this._nativeEditors();
    } catch (err) { this._error = err.message || String(err); }
    finally { this._loading = false; this._render(); }
  }
  async _refreshStatus() {
    try {
      const result = await this.hass.callWS({ type: "profile_scheduler/get" });
      if (this._dirty || this._dialog) return;
      this._document = clone(result.document);
      this._revision = result.revision;
      this._status = result;
      this._syncSelection();
      this._render();
    } catch (err) { this._error = err.message || String(err); this._render(); }
  }
  _syncSelection() {
    const topics = this._document.topics;
    this._topic = topics.some((topic) => topic.id === this._topic) ? this._topic : topics[0]?.id;
    const topic = topics.find((item) => item.id === this._topic);
    this._selected = topic?.profiles.some((profile) => profile.id === this._selected) ? this._selected : topic?.profiles[0]?.id;
    this._day ??= "0";
  }
  _changed() { this._dirty = true; this._error = ""; this._render(); }
  async _save() {
    this._busy = true;
    this._render();
    try {
      await this.hass.callWS({ type: "profile_scheduler/save", document: clone(this._document), revision: this._revision });
      await this._load();
    } catch (err) {
      this._error = err.code === "conflict" ? this._t("conflict") : err.message || String(err);
    } finally { this._busy = false; this._render(); }
  }
  async _mutate(command) {
    if (this._dirty) { this._error = this._t("unsaved"); this._render(); return; }
    this._busy = true;
    try { await this.hass.callWS(command); await this._load(); }
    catch (err) { this._error = err.message || String(err); }
    finally { this._busy = false; this._render(); }
  }
  async _confirm(text) {
    if (!this._helpers) throw new Error(this._t("unavailable"));
    return this._helpers.showConfirmationDialog(this, { title: text, confirmText: this._t("remove"), dismissText: this._t("cancel"), destructive: true });
  }
  _form(schema, data, update) {
    const form = el("ha-form");
    form.hass = this.hass;
    form.schema = schema;
    form.data = data;
    form.computeLabel = (item) => item.label || this._t(item.name);
    form.addEventListener("value-changed", (event) => { event.stopPropagation(); update(event.detail.value); });
    return form;
  }

  async _editor(kind, profile, row, existing, startMinute = 0, commitRow = () => {}) {
    if (this._busy || this._dialog) return;
    if (!await this._nativeEditors()) { this._error = this._t("bootstrap"); this._render(); return; }
    const draft = clone(existing || (kind === "topic" ? { id: newId(), name: "", entities: [], active_profile: null, profiles: [] }
      : kind === "profile" ? { id: newId(), name: "", schedule_mode: "daily", schedules: { all: [] } }
      : kind === "row" ? { id: newId(), name: "", entity_ids: [] }
        : { id: newId(), label: "", start: clock(startMinute), end: clock(Math.min(1440, startMinute + 30)), mode: "state", color: COLORS[0], actions: [] }));
    // A native prompt loads HA's dialog bundle through the public helper when
    // it has not yet been imported in this browser session.
    if (!customElements.get("ha-dialog")) {
      const name = await this._helpers.showPromptDialog(this, { title: this._t(kind === "block" ? "label" : "name"), defaultValue: draft.name || draft.label || "" });
      if (name === null) return;
      draft[kind === "block" ? "label" : "name"] = name;
    }
    if (!customElements.get("ha-dialog")) { this._error = this._t("unavailable"); this._render(); return; }
    const dialog = el("ha-dialog");
    dialog.headerTitle = this._t(`${existing ? "edit" : "add"}${kind[0].toUpperCase()}${kind.slice(1)}`);
    dialog.setAttribute("heading", dialog.headerTitle); // compatible pre-WebAwesome HA dialogs
    dialog.width = "large";
    dialog.open = true;
    const body = el("div", undefined, "editor-body");
    const dialogError = el("p", "", "error");
    dialogError.setAttribute("role", "alert");
    let form;
    if (kind === "topic" || kind === "profile") {
      const schema = [{ name: "name", required: true, selector: { text: {} } }];
      if (kind === "profile") schema.push({ name: "schedule_mode", selector: { select: { options: [
        { value: "daily", label: this._t("daily") }, { value: "weekly", label: this._t("weekly") },
      ] } } });
      form = this._form(schema, { name: draft.name, schedule_mode: draft.schedule_mode }, (value) => {
        draft.name = value.name;
        if (kind === "profile" && value.schedule_mode) draft.schedule_mode = value.schedule_mode;
      });
    } else if (kind === "row") {
      form = this._form([
        { name: "name", required: true, selector: { text: {} } },
        { name: "entity_ids", selector: { entity: { multiple: true } } },
      ], { name: draft.name, entity_ids: draft.entity_ids }, (value) => {
        draft.name = value.name;
        draft.entity_ids = value.entity_ids || [];
      });
    } else {
      form = this._form([
        { name: "label", required: true, selector: { text: {} } },
        { name: "start", required: true, selector: { text: {} } },
        { name: "end", required: true, selector: { text: {} } },
        { name: "mode", selector: { select: { options: [{ value: "state", label: this._t("state") }, { value: "once", label: this._t("once") }] } } },
        { name: "color", selector: { select: { options: COLORS.map((value, i) => ({ value, label: this._t("colors")[i] })) } } },
      ], Object.fromEntries(["label", "start", "end", "mode", "color"].map((key) => [key, draft[key]])), (value) => {
        for (const key of ["label", "start", "end", "mode", "color"]) {
          if (key in value) draft[key] = value[key];
        }
      });
    }
    body.append(form);
    if (kind === "block") {
      const actions = el("ha-selector");
      actions.hass = this.hass;
      actions.narrow = !!this._narrow;
      actions.selector = { action: { optionsInSidebar: false } };
      actions.label = this._t("actions");
      actions.value = draft.actions;
      const valueForms = [];
      const values = el("div");
      for (const entityId of new Set(row.entity_ids)) {
        const control = valueControl(entityId, this.hass, (key) => this._t(key));
        if (!control) continue;
        const current = (action) => readSimpleValue(action, entityId, control);
        const sync = () => {
          const value = draft.actions.map(current).findLast((item) => item !== undefined);
          valueForm.data = { value };
        };
        const name = this.hass.states[entityId].attributes.friendly_name || entityId;
        const valueForm = this._form([{ name: "value", label: name + " · " + control.label, selector: control.selector }], {}, ({ value }) => {
          const option = control.options?.find((item) => item.value === value);
          const limits = control.selector.number;
          const validNumber = limits && Number.isFinite(value) && value >= limits.min && value <= limits.max;
          if (!option && !validNumber) {
            sync();
            return;
          }
          const action = {
            action: control.service || control.domain + ".turn_" + value,
            target: { entity_id: [entityId] },
          };
          if (control.field) action.data = { [control.field]: value };
          const prior = draft.actions.findLastIndex((item) => current(item) !== undefined);
          if (prior < 0) draft.actions.push(action);
          else draft.actions[prior] = action;
          targetsInitialized = true;
          actions.value = clone(draft.actions);
          if (!draft.label.trim()) {
            const display = option?.label ?? [value, control.unit].filter((item) => item != null).join(" ");
            draft.label = display;
            form.data = { label: draft.label, start: draft.start, end: draft.end, mode: draft.mode, color: draft.color };
          }
          sync();
        });
        sync();
        valueForms.push(sync);
        values.append(valueForm);
      }
      if (valueForms.length) body.append(el("h3", this._t("entityValues")), values);
      let targetsInitialized = !!existing || draft.actions.length > 0;
      actions.addEventListener("value-changed", (event) => {
        event.stopPropagation();
        draft.actions = clone(Array.isArray(event.detail.value) ? event.detail.value : [event.detail.value]);
        if (!targetsInitialized && draft.actions.length === 1) {
          const action = draft.actions[0];
          if (action.action || action.service) {
            targetsInitialized = true;
            const hasTarget = Object.values(action.target || {}).some((value) => Array.isArray(value) ? value.length > 0 : !!value);
            if (row.entity_ids.length && !hasTarget && !action.data?.entity_id) action.target = { entity_id: [...row.entity_ids] };
          }
        }
        // HA action selectors are controlled elements: feed every edit back,
        // including edits to existing sequences and rows without default targets.
        actions.value = clone(draft.actions);
        for (const sync of valueForms) sync();
      });
      body.append(el("p", this._t("stateHelp")), el("p", this._t("actionHelp")), actions);
    }
    body.append(dialogError);
    const footer = el("div", undefined, "footer");
    footer.slot = "footer";
    const close = () => { dialog.open = false; dialog.remove(); this._dialog = undefined; };
    if (existing) footer.append(this._button(this._t("remove"), async () => {
      if (!await this._confirm(this._t("confirm"))) return;
      const topic = this._document.topics.find((item) => item.id === this._topic);
      if (kind === "topic") {
        this._document.topics = this._document.topics.filter((item) => item.id !== draft.id);
        this._syncSelection();
      } else if (kind === "profile") {
        topic.profiles = topic.profiles.filter((item) => item.id !== draft.id);
        if (topic.active_profile === draft.id) topic.active_profile = null;
        this._syncSelection();
      } else if (kind === "row") {
        topic.entities = topic.entities.filter((item) => item.id !== draft.id);
        for (const item of topic.profiles) for (const key of Object.keys(item.schedules)) {
          item.schedules[key] = item.schedules[key].filter((entry) => entry.id !== draft.id);
        }
      } else row.blocks.splice(row.blocks.findIndex((block) => block.id === draft.id), 1);
      close(); this._changed();
    }, true));
    footer.append(this._button(this._t("cancel"), close, true), this._button(this._t("save"), async () => {
      if (!(draft.name || draft.label || "").trim()) { dialogError.textContent = this._t("blankName"); return; }
      if (kind === "block") {
        if (!/^([01]\d|2[0-3]):[0-5]\d$/.test(draft.start) || !/^(([01]\d|2[0-3]):[0-5]\d|24:00)$/.test(draft.end) || draft.start === draft.end) {
          dialogError.textContent = this._t("overlap"); return;
        }
        if (!draft.actions.length) { dialogError.textContent = this._t("chooseAction"); return; }
      }
      const topic = this._document.topics.find((item) => item.id === this._topic);
      if (kind === "row" && existing) {
        const rows = topic.profiles.flatMap((item) => Object.values(item.schedules).flat().filter((entry) => entry.id === existing.id));
        if (existing.entity_ids.length && !draft.entity_ids.length && rows.some((entry) => entry.blocks.length)) {
          dialogError.textContent = this._t("clearRowTargets"); return;
        }
        const previous = existing.entity_ids;
        const matches = (value) => {
          const ids = Array.isArray(value) ? value : [value];
          return previous.length > 0 && ids.length === previous.length &&
            [...ids].sort().every((id, index) => id === [...previous].sort()[index]);
        };
        if (draft.entity_ids.length) for (const entry of rows) for (const block of entry.blocks) for (const action of block.actions) {
          if (!action.action && !action.service) continue;
          const target = action.target || {};
          if (Object.entries(target).some(([key, value]) => key !== "entity_id" && (Array.isArray(value) ? value.length : value))) continue;
          const fields = [target, action.data].filter((value) => value && Object.hasOwn(value, "entity_id"));
          if (!fields.length || !fields.every((value) => matches(value.entity_id))) continue;
          for (const value of fields) value.entity_id = draft.entity_ids.length === 1 && !Array.isArray(value.entity_id) ? draft.entity_ids[0] : [...draft.entity_ids];
        }
      }
      if (kind === "profile" && existing && draft.schedule_mode !== existing.schedule_mode) {
        if (!await this._confirm(this._t("changeMode"))) return;
        const source = existing.schedules[existing.schedule_mode === "daily" ? "all" : this._day] || [];
        draft.schedules = draft.schedule_mode === "daily" ? { all: clone(source) }
          : Object.fromEntries(Array.from({ length: 7 }, (_, day) => [String(day), clone(source)]));
      } else if (kind === "profile" && !existing && draft.schedule_mode === "weekly") {
        draft.schedules = Object.fromEntries(Array.from({ length: 7 }, (_, day) => [String(day), []]));
      }
      const items = kind === "topic" ? this._document.topics : kind === "profile" ? topic.profiles : kind === "row" ? topic.entities : row.blocks;
      const index = items.findIndex((item) => item.id === draft.id);
      if (index < 0) items.push(draft); else items[index] = draft;
      if (kind === "topic") { this._topic = draft.id; if (!existing) this._selected = undefined; }
      if (kind === "profile") this._selected = draft.id;
      if (kind === "block") commitRow();
      close(); this._changed();
    }));
    dialog.append(body, footer);
    dialog.addEventListener("closed", () => { if (this._dialog === dialog) close(); });
    this._dialog = dialog;
    this.shadowRoot.append(dialog);
  }

  _render() {
    // Never detach a live native dialog: disconnecting it can reset its editor.
    if (this._dialog) return;
    this.shadowRoot.replaceChildren();
    const style = el("style");
    style.textContent = `
      :host{display:block;height:100%;overflow:auto;background:var(--primary-background-color);color:var(--primary-text-color);font-family:var(--ha-font-family-body,Roboto,sans-serif)}
      *{box-sizing:border-box} main{padding:24px;max-width:1600px;margin:auto} h1{font-size:24px} h2{font-size:20px}
      .toolbar,.status,.footer{display:flex;align-items:center;gap:12px;flex-wrap:wrap}.toolbar{margin:16px 0}.status{padding:16px;border-radius:var(--ha-card-border-radius,12px);background:var(--card-background-color)}
      .error{color:var(--error-color);white-space:pre-wrap}.notice{padding:16px;background:var(--card-background-color);border:1px solid var(--divider-color);border-radius:12px}
      .profiles{display:flex;gap:8px;flex-wrap:wrap}.sections{display:flex;gap:8px;overflow-x:auto;padding:8px 4px;white-space:nowrap}.selected{outline:2px solid var(--primary-color);border-radius:var(--ha-card-border-radius,12px)}
      .scroll{overflow-x:auto;padding:4px}.grid{min-width:850px}.row{display:grid;grid-template-columns:200px 1fr;gap:12px;margin-bottom:12px}.row-label{display:flex;flex-direction:column;align-items:flex-start;gap:4px;overflow-wrap:anywhere}
      .track{position:relative;height:64px;background:repeating-linear-gradient(to right,var(--divider-color) 0,var(--divider-color) 1px,transparent 1px,transparent calc(100% / 48));border:1px solid var(--divider-color);border-radius:8px}
      .ticks{display:flex;justify-content:space-between;font-size:12px;color:var(--secondary-text-color)}.ticks span:last-child{transform:translateX(-2px)}
      .block-list{display:flex;flex-wrap:wrap;gap:4px;margin-top:4px}.block-list ha-button{font-size:12px}
      .block{position:absolute;top:4px;bottom:4px;min-width:8px;border:1px solid #fff;border-radius:6px;color:#fff;font:inherit;font-size:12px;overflow:hidden;text-align:start;padding:3px 5px;cursor:pointer;text-shadow:0 1px 2px #000}
      .block:focus-visible{outline:3px solid var(--primary-text-color);z-index:2}.block span{display:block;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
      small{color:var(--secondary-text-color)} .editor-body{padding:16px;min-width:min(70vw,700px)} .footer{padding:12px;justify-content:flex-end}ha-form{display:block;margin-bottom:16px}
      a{color:var(--primary-color)}@media(max-width:600px){main{padding:12px}.editor-body{min-width:0}.row{grid-template-columns:150px 1fr}}
    `;
    this.shadowRoot.append(style);
    const main = el("main");
    const header = el("div", undefined, "toolbar");
    const menu = el("ha-menu-button");
    menu.hass = this.hass;
    menu.narrow = !!this._narrow;
    header.append(menu, el("h1", this._t("title")));
    main.append(header);
    if (this._error) { const error = el("p", this._error, "error"); error.setAttribute("role", "alert"); main.append(error); }
    if (!this._loaded) { main.append(this._button(this._t("reload"), () => this._load())); this.shadowRoot.append(main); return; }
    if (!this._editors) {
      const notice = el("div", undefined, "notice");
      const link = el("a", this._t("dashboard")); link.href = "/lovelace/0";
      notice.append(el("p", this._t("bootstrap")), link, this._button(this._t("retry"), async () => {
        try { if (!await this._nativeEditors()) this._error = this._t("unavailable"); } catch (err) { this._error = err.message; }
        this._render();
      }));
      main.append(notice);
    }
    const status = el("div", undefined, "status");
    const topic = this._document.topics.find((item) => item.id === this._topic);
    const active = topic?.profiles.find((item) => item.id === topic.active_profile);
    const due = this._status.next_change ? new Date(this._status.next_change).toLocaleString(this.hass.language, { timeZone: this.hass.config.time_zone }) : "—";
    status.append(el("strong", this._t(this._document.enabled ? "enabled" : "disabled")),
      el("span", `${this._t("active")}: ${active?.name || this._t("noProfile")}`), el("span", `${this._t("next")}: ${due}`),
      this._button(this._t(this._document.enabled ? "disable" : "enable"), () => this._mutate({ type: "profile_scheduler/set_enabled", enabled: !this._document.enabled })));
    main.append(status);
    if (this._status.last_error) main.append(el("p", this._status.last_error, "error"));
    const toolbar = el("div", undefined, "toolbar");
    toolbar.append(this._button(this._t("save"), () => this._save()), this._button(this._t("reload"), async () => {
      if (this._dirty && !await this._confirm(this._t("discard"))) return;
      await this._load();
    }, true), el("span", this._t(this._dirty ? "unsaved" : "saved")));
    main.append(toolbar);
    const topicTabs = el("div", undefined, "profiles");
    for (const item of this._document.topics) {
      const tab = this._button(item.name, () => { this._topic = item.id; this._selected = item.profiles[0]?.id; this._render(); }, true);
      tab.setAttribute("aria-pressed", String(item.id === this._topic));
      if (item.id === this._topic) tab.className = "selected";
      topicTabs.append(tab);
    }
    topicTabs.append(this._button(this._t("addTopic"), () => this._editor("topic"), true));
    main.append(el("h2", this._t("topics")), topicTabs);
    if (topic) {
      this._section ??= "entities";
      const sectionNav = el("nav", undefined, "sections");
      sectionNav.setAttribute("aria-label", this._t("topics"));
      for (const [section, label] of [["entities", "sectionEntities"], ["profiles", "sectionProfiles"], ["plan", "sectionPlan"]]) {
        const button = this._button(this._t(label), () => { this._section = section; this._render(); }, true);
        button.setAttribute("aria-pressed", String(this._section === section));
        if (this._section === section) button.className = "selected";
        sectionNav.append(button);
      }
      main.append(sectionNav);
      const topicControls = el("div", undefined, "toolbar");
      topicControls.append(this._button(this._t("editTopic"), () => this._editor("topic", undefined, undefined, topic), true));
      if (this._section === "entities") topicControls.append(this._button(this._t("addRow"), () => this._editor("row"), true));
      main.append(topicControls);
      if (this._section === "entities") for (const entity of topic.entities) {
        const item = el("div", undefined, "toolbar");
        item.append(el("strong", entity.name), el("small", entity.entity_ids.map((id) => this.hass.states[id]?.attributes.friendly_name || id).join(", ") || this._t("group")),
          this._button(this._t("editRow"), () => this._editor("row", undefined, entity, entity), true));
        main.append(item);
      }
      if (this._section === "profiles" && this._editors) main.append(this._form([{ name: "active", label: this._t("active"), selector: { select: { options: [
        { value: "__none__", label: this._t("noProfile") }, ...topic.profiles.map((item) => ({ value: item.id, label: item.name })),
      ] } } }], { active: topic.active_profile || "__none__" }, (value) => {
        void this._mutate({ type: "profile_scheduler/set_profile", topic_id: topic.id, profile_id: value.active === "__none__" ? null : value.active });
      }));
      if (this._section !== "entities") {
        const tabs = el("div", undefined, "profiles");
        for (const item of topic.profiles) {
          const tab = this._button(item.name, () => { this._selected = item.id; this._render(); }, true);
          tab.setAttribute("aria-pressed", String(this._selected === item.id));
          if (this._selected === item.id) tab.className = "selected";
          tabs.append(tab);
        }
        if (this._section === "profiles") tabs.append(this._button(this._t("addProfile"), () => this._editor("profile"), true));
        main.append(el("h2", this._t("profiles")), tabs);
      }
    }
    const profile = topic?.profiles.find((item) => item.id === this._selected);
    if (profile && this._section === "profiles") {
      const controls = el("div", undefined, "toolbar");
      controls.append(this._button(this._t("editProfile"), () => this._editor("profile", profile, undefined, profile), true));
      main.append(controls);
    }
    if (profile && this._section === "plan") {
      if (profile.schedule_mode === "weekly" && this._editors) main.append(this._form([
        { name: "day", label: this._t("day"), selector: { select: { options: this._t("days").map((label, i) => ({ label, value: String(i) })) } } },
      ], { day: this._day }, (value) => { this._day = value.day; this._render(); }));
      if (!topic.entities.length) main.append(el("p", this._t("noRows")));
      const key = profile.schedule_mode === "daily" ? "all" : this._day;
      const schedule = profile.schedules[key] || [];
      const scroll = el("div", undefined, "scroll");
      const grid = el("div", undefined, "grid");
      const axis = el("div", undefined, "row");
      const ticks = el("div", undefined, "ticks");
      for (let hour = 0; hour <= 24; hour += 3) ticks.append(el("span", `${String(hour).padStart(2, "0")}:00`));
      axis.append(el("div"), ticks); grid.append(axis);
      for (const entity of topic.entities) {
        const entry = schedule.find((item) => item.id === entity.id);
        // A missing row is created only when a block is actually saved.
        const row = { ...entity, blocks: entry?.blocks || [] };
        const commitRow = () => { if (!entry && row.blocks.length) { (profile.schedules[key] ||= []).push({ id: entity.id, blocks: row.blocks }); } };
        const editBlock = async (block, minute) => { await this._editor("block", profile, row, block, minute, commitRow); };
        const line = el("div", undefined, "row");
        const label = el("div", undefined, "row-label");
        label.append(el("strong", row.name), el("small", row.entity_ids.map((id) => this.hass.states[id]?.attributes.friendly_name || id).join(", ") || this._t("group")),
          this._button(this._t("addBlock"), () => editBlock(), true));
        const track = el("div", undefined, "track");
        track.setAttribute("aria-label", `${row.name}: ${this._t("timeAxis")}`);
        track.addEventListener("click", (event) => {
          if (event.target !== track) return;
          const rect = track.getBoundingClientRect();
          const minute = Math.max(0, Math.min(1410, Math.floor((event.clientX - rect.left) / rect.width * 48) * 30));
          void editBlock(undefined, minute);
        });
        for (const block of row.blocks) {
          const begin = minutes(block.start), end = minutes(block.end);
          const pieces = end < begin ? [[begin, 1440], [0, end]] : [[begin, end]];
          for (const [left, right] of pieces) {
            if (right <= left) continue;
            const button = el("button", undefined, "block");
            button.style.left = `${left / 14.4}%`; button.style.width = `${(right - left) / 14.4}%`;
            button.style.backgroundColor = COLORS.includes(block.color) ? block.color : COLORS[0];
            button.title = `${block.label}: ${block.start}–${block.end} · ${this._t(block.mode)}`;
            button.setAttribute("aria-label", button.title);
            button.append(el("span", block.label), el("span", `${block.start}–${block.end} ${block.mode === "once" ? "▶" : "↻"}`));
            button.addEventListener("click", (event) => { event.stopPropagation(); void editBlock(block); });
            track.append(button);
          }
        }
        const timeline = el("div");
        const blockList = el("div", undefined, "block-list");
        for (const block of [...row.blocks].sort((a, b) => minutes(a.start) - minutes(b.start))) {
          blockList.append(this._button(`${block.start}–${block.end} · ${block.label} · ${this._t(block.mode)}`,
            () => editBlock(block), true));
        }
        timeline.append(track, blockList);
        line.append(label, timeline); grid.append(line);
      }
      scroll.append(grid); main.append(scroll);
    } else if (topic && !profile && this._section === "plan") main.append(el("p", this._t("empty")));
    this.shadowRoot.append(main);
  }
}

if (!customElements.get("profile-scheduler-panel")) customElements.define("profile-scheduler-panel", ProfileSchedulerPanel);
