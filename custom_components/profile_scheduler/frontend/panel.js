/* Native HA controls surround the only custom UI: the daily timeline. */
const TEXT = {
  cs: {
    title: "Scheduler", profiles: "Profily", addProfile: "Přidat profil", editProfile: "Upravit profil",
    addRow: "Přidat řádek", editRow: "Upravit řádek", addBlock: "Přidat úsek", editBlock: "Upravit úsek",
    name: "Název", weekdays: "Dny pro automatický výběr", entities: "Výchozí cílové entity",
    start: "Začátek (HH:MM)", end: "Konec (HH:MM nebo 24:00)", label: "Hodnota nebo popisek akce",
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
    actionHelp: "Cíle a parametry upravte přímo v nativním editoru akcí. Cíle řádku se předvyplní pouze do první nově vytvořené akce.",
    overlap: "Časy musí mít formát HH:MM a úseky jednoho řádku se nesmějí překrývat.",
    chooseAction: "Přidejte alespoň jednu akci v editoru Home Assistantu.", conflict: "Plán se mezitím změnil. Neuložený návrh zůstal zde; zkopírujte jej nebo znovu načtěte aktuální plán.",
    discard: "Zahodit neuložené změny a načíst uložený plán?", blankName: "Vyplňte název nebo popisek.",
    group: "Skupina akcí", timeAxis: "Denní časová osa od 00:00 do 24:00, krok 30 minut",
    colors: ["Modrá", "Zelená", "Oranžová", "Fialová", "Červená", "Tyrkysová"],
    days: ["Pondělí", "Úterý", "Středa", "Čtvrtek", "Pátek", "Sobota", "Neděle"],
  },
  en: {
    title: "Scheduler", profiles: "Profiles", addProfile: "Add profile", editProfile: "Edit profile",
    addRow: "Add row", editRow: "Edit row", addBlock: "Add time block", editBlock: "Edit time block",
    name: "Name", weekdays: "Days for automatic selection", entities: "Default target entities",
    start: "Start (HH:MM)", end: "End (HH:MM or 24:00)", label: "Value or action label",
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
    actionHelp: "Edit targets and parameters in the native action editor. Row targets prefill only the first newly created action.",
    overlap: "Use HH:MM times; blocks in the same row must not overlap.",
    chooseAction: "Add at least one action in the Home Assistant editor.", conflict: "The schedule changed elsewhere. Your draft is still here; copy it or reload the current schedule.",
    discard: "Discard unsaved changes and reload the saved schedule?", blankName: "Enter a name or label.",
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
      this._selected = this._document.profiles.some((p) => p.id === this._selected) ? this._selected : this._document.profiles[0]?.id;
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
      this._render();
    } catch (err) { this._error = err.message || String(err); this._render(); }
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

  async _editor(kind, profile, row, existing, startMinute = 0) {
    if (this._busy || this._dialog) return;
    if (!await this._nativeEditors()) { this._error = this._t("bootstrap"); this._render(); return; }
    const draft = clone(existing || (kind === "profile" ? { id: newId(), name: "", weekdays: [], rows: [] }
      : kind === "row" ? { id: newId(), name: "", entity_ids: [], blocks: [] }
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
    if (kind === "profile") {
      form = this._form([
        { name: "name", required: true, selector: { text: {} } },
        { name: "weekdays", selector: { select: { multiple: true, options: this._t("days").map((label, i) => ({ label, value: String(i) })) } } },
      ], { ...draft, weekdays: draft.weekdays.map(String) }, (value) => { draft.name = value.name; draft.weekdays = (value.weekdays || []).map(Number); });
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
      body.append(el("p", this._t("stateHelp")), el("p", this._t("actionHelp")));
      const actions = el("ha-selector");
      actions.hass = this.hass;
      actions.narrow = !!this._narrow;
      actions.selector = { action: { optionsInSidebar: false } };
      actions.label = this._t("actions");
      actions.value = draft.actions;
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
      });
      body.append(actions);
    }
    body.append(dialogError);
    const footer = el("div", undefined, "footer");
    footer.slot = "footer";
    const close = () => { dialog.open = false; dialog.remove(); this._dialog = undefined; };
    if (existing) footer.append(this._button(this._t("remove"), async () => {
      if (!await this._confirm(this._t("confirm"))) return;
      if (kind === "profile") {
        this._document.profiles = this._document.profiles.filter((p) => p.id !== draft.id);
        if (this._document.manual_profile === draft.id) this._document.manual_profile = null;
        this._selected = this._document.profiles[0]?.id;
      } else if (kind === "row") profile.rows = profile.rows.filter((r) => r.id !== draft.id);
      else row.blocks = row.blocks.filter((b) => b.id !== draft.id);
      close(); this._changed();
    }, true));
    footer.append(this._button(this._t("cancel"), close, true), this._button(this._t("save"), () => {
      if (!(draft.name || draft.label || "").trim()) { dialogError.textContent = this._t("blankName"); return; }
      if (kind === "block") {
        if (!/^([01]\d|2[0-3]):[0-5]\d$/.test(draft.start) || !/^(([01]\d|2[0-3]):[0-5]\d|24:00)$/.test(draft.end) || draft.start === draft.end) {
          dialogError.textContent = this._t("overlap"); return;
        }
        if (!draft.actions.length) { dialogError.textContent = this._t("chooseAction"); return; }
      }
      const items = kind === "profile" ? this._document.profiles : kind === "row" ? profile.rows : row.blocks;
      const index = items.findIndex((item) => item.id === draft.id);
      if (index < 0) items.push(draft); else items[index] = draft;
      if (kind === "profile") this._selected = draft.id;
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
      .profiles{display:flex;gap:8px;flex-wrap:wrap}.selected{outline:2px solid var(--primary-color);border-radius:var(--ha-card-border-radius,12px)}
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
    const active = this._document.profiles.find((p) => p.id === this._status.active_profile);
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
    if (this._editors) {
      main.append(this._form([{ name: "manual", selector: { select: { options: [{ value: "__auto__", label: this._t("automatic") }, ...this._document.profiles.map((p) => ({ value: p.id, label: p.name }))] } } }],
        { manual: this._document.manual_profile || "__auto__" }, (value) => { void this._mutate({ type: "profile_scheduler/set_profile", profile_id: value.manual === "__auto__" ? null : value.manual }); }));
    }
    const tabs = el("div", undefined, "profiles");
    for (const profile of this._document.profiles) {
      const tab = this._button(profile.name, () => { this._selected = profile.id; this._render(); }, true);
      tab.setAttribute("aria-pressed", String(this._selected === profile.id));
      if (this._selected === profile.id) tab.className = "selected";
      tabs.append(tab);
    }
    tabs.append(this._button(this._t("addProfile"), () => this._editor("profile"), true));
    main.append(el("h2", this._t("profiles")), tabs);
    const profile = this._document.profiles.find((p) => p.id === this._selected);
    if (profile) {
      const controls = el("div", undefined, "toolbar");
      controls.append(this._button(this._t("editProfile"), () => this._editor("profile", profile, undefined, profile), true),
        this._button(this._t("addRow"), () => this._editor("row", profile), true));
      main.append(controls);
      if (!profile.rows.length) main.append(el("p", this._t("noRows")));
      const scroll = el("div", undefined, "scroll");
      const grid = el("div", undefined, "grid");
      const axis = el("div", undefined, "row");
      const ticks = el("div", undefined, "ticks");
      for (let hour = 0; hour <= 24; hour += 3) ticks.append(el("span", `${String(hour).padStart(2, "0")}:00`));
      axis.append(el("div"), ticks); grid.append(axis);
      for (const row of profile.rows) {
        const line = el("div", undefined, "row");
        const label = el("div", undefined, "row-label");
        label.append(el("strong", row.name), el("small", row.entity_ids.map((id) => this.hass.states[id]?.attributes.friendly_name || id).join(", ") || this._t("group")),
          this._button(this._t("editRow"), () => this._editor("row", profile, row, row), true),
          this._button(this._t("addBlock"), () => this._editor("block", profile, row), true));
        const track = el("div", undefined, "track");
        track.setAttribute("aria-label", `${row.name}: ${this._t("timeAxis")}`);
        track.addEventListener("click", (event) => {
          if (event.target !== track) return;
          const rect = track.getBoundingClientRect();
          const minute = Math.max(0, Math.min(1410, Math.floor((event.clientX - rect.left) / rect.width * 48) * 30));
          void this._editor("block", profile, row, undefined, minute);
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
            button.addEventListener("click", (event) => { event.stopPropagation(); void this._editor("block", profile, row, block); });
            track.append(button);
          }
        }
        const timeline = el("div");
        const blockList = el("div", undefined, "block-list");
        for (const block of [...row.blocks].sort((a, b) => minutes(a.start) - minutes(b.start))) {
          blockList.append(this._button(`${block.start}–${block.end} · ${block.label} · ${this._t(block.mode)}`,
            () => this._editor("block", profile, row, block), true));
        }
        timeline.append(track, blockList);
        line.append(label, timeline); grid.append(line);
      }
      scroll.append(grid); main.append(scroll);
    } else main.append(el("p", this._t("empty")));
    this.shadowRoot.append(main);
  }
}

if (!customElements.get("profile-scheduler-panel")) customElements.define("profile-scheduler-panel", ProfileSchedulerPanel);
