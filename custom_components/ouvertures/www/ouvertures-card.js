/**
 * custom:ouvertures-card — carte visuelle Gestion des ouvertures
 * Affiche le SVG d'état et les boutons de commande selon le type.
 *
 * Important : ne reconstruit le DOM que si l'état utile change
 * (évite le clignotement des images à chaque push hass).
 */
(() => {
  const CARD_VERSION = "1.1.3";
  const CARD_TYPE = "ouvertures-card";
  const NO_AREA = "Sans pièce";

  const OPEN_TYPES_WITH_CONTROLS = new Set([
    "portail_coulissant",
    "garage_sectionnelle",
  ]);

  const STYLES = `
    :host { display: block; }
    ha-card {
      padding: 12px;
      background: linear-gradient(165deg, #f8fafc 0%, #eef2ff 45%, #f1f5f9 100%);
      overflow: hidden;
    }
    .ov-title {
      font-size: 1.15rem;
      font-weight: 700;
      letter-spacing: 0.01em;
      margin: 0 4px 12px;
      color: #1f2937;
    }
    .ov-groups {
      display: flex;
      flex-direction: column;
      gap: 18px;
    }
    .ov-group-title {
      font-size: 1.05rem;
      font-weight: 750;
      color: #0f172a;
      margin: 0 4px 10px;
      padding-bottom: 6px;
      border-bottom: 1px solid rgba(148, 163, 184, 0.45);
      display: flex;
      align-items: center;
      gap: 8px;
    }
    .ov-group-title::before {
      content: "";
      width: 8px;
      height: 8px;
      border-radius: 50%;
      background: #64748b;
      flex-shrink: 0;
    }
    .ov-grid {
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(180px, 1fr));
      gap: 12px;
    }
    .ov-single { display: block; max-width: 280px; margin: 0 auto; }
    .ov-tile {
      display: flex;
      flex-direction: column;
      align-items: center;
      gap: 8px;
      padding: 10px 8px 12px;
      border-radius: 16px;
      background: rgba(255,255,255,0.72);
      border: 1px solid rgba(148,163,184,0.35);
      transition: box-shadow 0.2s ease, border-color 0.2s ease, background 0.2s ease;
    }
    .ov-tile:hover {
      box-shadow: 0 8px 20px rgba(15, 23, 42, 0.08);
    }
    .ov-tile.is-alert {
      border-color: rgba(234, 88, 12, 0.55);
      background: rgba(255, 247, 237, 0.9);
    }
    .ov-tile.is-ok {
      border-color: rgba(22, 163, 74, 0.35);
    }
    .ov-area {
      font-weight: 750;
      font-size: 1.05rem;
      color: #0f172a;
      text-align: center;
      line-height: 1.2;
    }
    .ov-name {
      font-weight: 550;
      font-size: 0.82rem;
      color: #64748b;
      text-align: center;
      line-height: 1.2;
    }
    .ov-name.ov-name-only {
      font-weight: 700;
      font-size: 0.98rem;
      color: #111827;
    }
    .ov-visual {
      border: 0;
      background: transparent;
      padding: 0;
      cursor: pointer;
      width: 100%;
      display: flex;
      justify-content: center;
    }
    .ov-visual img {
      width: min(100%, 220px);
      aspect-ratio: 1;
      object-fit: contain;
      display: block;
      filter: drop-shadow(0 4px 10px rgba(15,23,42,0.12));
    }
    .ov-label {
      font-size: 0.8rem;
      color: #4b5563;
      text-align: center;
      min-height: 2.2em;
    }
    .ov-tile.is-alert .ov-label {
      color: #c2410c;
      font-weight: 600;
    }
    .ov-controls {
      display: flex;
      flex-wrap: wrap;
      gap: 6px;
      justify-content: center;
      width: 100%;
      margin-top: 2px;
    }
    .ov-btn {
      border: 0;
      border-radius: 10px;
      padding: 7px 12px;
      font-size: 0.78rem;
      font-weight: 650;
      cursor: pointer;
      color: #fff;
      background: #374151;
      transition: filter 0.15s ease, transform 0.15s ease;
    }
    .ov-btn:hover { filter: brightness(1.08); }
    .ov-btn:active { transform: scale(0.97); }
    .ov-btn.ov-open { background: #16a34a; }
    .ov-btn.ov-close { background: #4b5563; }
    .ov-btn.ov-impulse { background: #ea580c; }
    .ov-missing {
      min-height: 160px;
      justify-content: center;
      color: #b91c1c;
    }
    .ov-hint { color: #6b7280; font-size: 0.9rem; padding: 4px; }
    @media (max-width: 500px) {
      .ov-grid { grid-template-columns: 1fr 1fr; gap: 8px; }
      .ov-name { font-size: 0.85rem; }
      .ov-btn { padding: 6px 8px; font-size: 0.72rem; }
    }
  `;

  function fireEvent(node, type, detail = {}, options = {}) {
    const event = new Event(type, {
      bubbles: options.bubbles !== undefined ? options.bubbles : true,
      cancelable: Boolean(options.cancelable),
      composed: options.composed !== undefined ? options.composed : true,
    });
    event.detail = detail;
    node.dispatchEvent(event);
    return event;
  }

  class OuverturesCardEditor extends HTMLElement {
    setConfig(config) {
      this._config = { ...config };
      this._render();
    }

    set hass(hass) {
      this._hass = hass;
    }

    _render() {
      if (!this._config) return;
      this.innerHTML = `
        <div class="card-config" style="display:flex;flex-direction:column;gap:12px;padding:4px 0;">
          <ha-textfield
            label="Titre (optionnel)"
            .value="${this._config.title || ""}"
            data-key="title"
          ></ha-textfield>
          <ha-entity-picker
            label="Capteur État (sensor.xxx)"
            .value="${this._config.entity || ""}"
            data-key="entity"
            allow-custom-entity
          ></ha-entity-picker>
          <ha-textfield
            label="Entités (séparées par des virgules, mode grille)"
            .value="${(this._config.entities || []).join(", ")}"
            data-key="entities"
            helper="Laissez vide pour une seule carte"
          ></ha-textfield>
        </div>
      `;
      this.querySelectorAll("ha-textfield, ha-entity-picker").forEach((el) => {
        el.addEventListener("value-changed", (ev) => {
          const key = el.getAttribute("data-key");
          const newConfig = { ...this._config };
          let value = ev.detail?.value ?? el.value;
          if (key === "entities") {
            value = String(value || "")
              .split(",")
              .map((s) => s.trim())
              .filter(Boolean);
            if (!value.length) delete newConfig.entities;
            else newConfig.entities = value;
          } else if (!value) {
            delete newConfig[key];
          } else {
            newConfig[key] = value;
          }
          fireEvent(this, "config-changed", { config: newConfig });
        });
        el.addEventListener("change", () => {
          const key = el.getAttribute("data-key");
          if (!key) return;
          const newConfig = { ...this._config };
          if (key === "entities") {
            const value = String(el.value || "")
              .split(",")
              .map((s) => s.trim())
              .filter(Boolean);
            if (!value.length) delete newConfig.entities;
            else newConfig.entities = value;
          } else if (!el.value) {
            delete newConfig[key];
          } else {
            newConfig[key] = el.value;
          }
          fireEvent(this, "config-changed", { config: newConfig });
        });
      });
    }
  }

  class OuverturesCard extends HTMLElement {
    constructor() {
      super();
      this._hass = null;
      this._config = null;
      this._root = null;
      this._built = false;
      this._lastSig = "";
      this._boundClick = (ev) => this._onClick(ev);
    }

    static getStubConfig(hass, entities) {
      const match =
        entities?.find?.(
          (e) =>
            typeof e === "string" &&
            e.startsWith("sensor.") &&
            e.endsWith("_etat")
        ) ||
        (hass &&
          Object.keys(hass.states || {}).find(
            (e) =>
              e.startsWith("sensor.") &&
              hass.states[e]?.attributes?.opening_type
          ));
      return match
        ? { entity: match, title: "Ouvertures" }
        : { title: "Ouvertures", entities: [] };
    }

    static async getConfigElement() {
      if (!customElements.get(`${CARD_TYPE}-editor`)) {
        customElements.define(`${CARD_TYPE}-editor`, OuverturesCardEditor);
      }
      return document.createElement(`${CARD_TYPE}-editor`);
    }

    setConfig(config) {
      if (!config || typeof config !== "object") {
        throw new Error("Configuration invalide");
      }
      this._config = { ...config };
      this._built = false;
      this._lastSig = "";
      if (this._hass) this._update(true);
    }

    set hass(hass) {
      this._hass = hass;
      this._update(false);
    }

    get hass() {
      return this._hass;
    }

    getCardSize() {
      if (this._config?.entities?.length) {
        return Math.ceil(this._config.entities.length / 2) * 4;
      }
      return 5;
    }

    _entities() {
      if (this._config.entities?.length) return this._config.entities;
      if (this._config.entity) return [this._config.entity];
      return [];
    }

    _attrs(entityId) {
      const st = this._hass?.states?.[entityId];
      if (!st) return null;
      const rawName =
        st.attributes.name ||
        st.attributes.friendly_name ||
        entityId;
      // Evite le suffixe " État" du friendly_name HA
      const name = String(rawName).replace(/\s+État$/i, "").trim();
      return {
        state: st.state,
        name,
        area: st.attributes.area || "",
        displayName: st.attributes.display_name || name,
        label: st.attributes.label || st.attributes.friendly_state || st.state,
        image: st.attributes.image || "",
        isAlert: Boolean(st.attributes.is_alert),
        isOpen: Boolean(st.attributes.is_open),
        openingType: st.attributes.opening_type,
        openEntity: st.attributes.open_entity,
        closeEntity: st.attributes.close_entity,
        impulseEntity: st.attributes.impulse_entity,
      };
    }

    /** Signature stable : rebuild seulement si ça change. */
    _signature(entities) {
      return entities
        .map((id) => {
          const st = this._hass?.states?.[id];
          if (!st) return `${id}|missing`;
          const a = st.attributes || {};
          return [
            id,
            st.state,
            a.image || "",
            a.label || "",
            a.area || "",
            a.display_name || "",
            a.name || "",
            a.is_alert ? 1 : 0,
            a.open_entity || "",
            a.close_entity || "",
            a.impulse_entity || "",
            a.opening_type || "",
          ].join("|");
        })
        .join(";");
    }

    _onClick(ev) {
      const btn = ev.target.closest("[data-entity].ov-btn");
      if (btn) {
        ev.stopPropagation();
        this._callButton(btn.getAttribute("data-entity"));
        return;
      }
      const more = ev.target.closest("[data-more]");
      if (more) {
        this._moreInfo(more.getAttribute("data-more"));
      }
    }

    async _callButton(entityId) {
      if (!entityId || !this._hass) return;
      const domain = entityId.split(".")[0];
      if (domain === "button") {
        await this._hass.callService("button", "press", { entity_id: entityId });
      } else if (domain === "input_button") {
        await this._hass.callService("input_button", "press", {
          entity_id: entityId,
        });
      } else if (domain === "script") {
        await this._hass.callService("script", "turn_on", { entity_id: entityId });
      } else if (domain === "switch") {
        await this._hass.callService("switch", "turn_on", { entity_id: entityId });
      } else if (domain === "cover") {
        await this._hass.callService("cover", "toggle", { entity_id: entityId });
      }
    }

    _moreInfo(entityId) {
      fireEvent(this, "hass-more-info", { entityId });
    }

    _resolveControls(info, entityId) {
      if (!OPEN_TYPES_WITH_CONTROLS.has(info.openingType)) return [];

      const base = entityId.replace(/_etat$/, "").replace(/^sensor\./, "");
      const guess = (suffix) => {
        const candidates = [
          `button.${base}_${suffix}`,
          `button.ouvertures_${base}_${suffix}`,
        ];
        for (const c of candidates) {
          if (this._hass.states[c]) return c;
        }
        return null;
      };

      const openBtn = info.openEntity || guess("ouvrir");
      const closeBtn = info.closeEntity || guess("fermer");
      const impulseBtn = info.impulseEntity || guess("impulsion");

      const buttons = [];
      if (info.openingType === "portail_coulissant") {
        if (openBtn) buttons.push({ cls: "ov-open", id: openBtn, label: "Ouvrir" });
        if (closeBtn)
          buttons.push({ cls: "ov-close", id: closeBtn, label: "Fermer" });
      }
      if (impulseBtn) {
        buttons.push({
          cls: "ov-impulse",
          id: impulseBtn,
          label: "Impulsion",
        });
      }
      return buttons;
    }

    _groupByArea(entities) {
      const groups = new Map();
      for (const entityId of entities) {
        const info = this._attrs(entityId);
        const area = (info && info.area) || NO_AREA;
        if (!groups.has(area)) groups.set(area, []);
        groups.get(area).push({ entityId, info });
      }
      return [...groups.entries()].sort(([a], [b]) => {
        if (a === NO_AREA) return 1;
        if (b === NO_AREA) return -1;
        return a.localeCompare(b, "fr", { sensitivity: "base" });
      });
    }

    _ensureShell(titleText) {
      if (!this._root) {
        this._root = document.createElement("ha-card");
        this.appendChild(this._root);
        this._root.addEventListener("click", this._boundClick);
      }

      if (!this._built) {
        this._root.innerHTML = "";
        const style = document.createElement("style");
        style.textContent = STYLES;
        this._root.appendChild(style);

        if (titleText) {
          const t = document.createElement("div");
          t.className = "ov-title";
          t.textContent = titleText;
          this._root.appendChild(t);
        }

        const groups = document.createElement("div");
        groups.className = "ov-groups";
        this._root.appendChild(groups);
        this._built = true;
      } else {
        const titleEl = this._root.querySelector(".ov-title");
        if (titleText) {
          if (!titleEl) {
            const t = document.createElement("div");
            t.className = "ov-title";
            t.textContent = titleText;
            this._root.insertBefore(t, this._root.querySelector(".ov-groups"));
          } else if (titleEl.textContent !== titleText) {
            titleEl.textContent = titleText;
          }
        } else if (titleEl) {
          titleEl.remove();
        }
      }
      return this._root.querySelector(".ov-groups");
    }

    _ensureGroup(groupsEl, areaName, multiGroup) {
      const key = areaName || NO_AREA;
      let group = groupsEl.querySelector(
        `.ov-group[data-area="${CSS.escape(key)}"]`
      );
      if (!group) {
        group = document.createElement("div");
        group.className = "ov-group";
        group.dataset.area = key;
        const title = document.createElement("div");
        title.className = "ov-group-title";
        title.textContent = key;
        const grid = document.createElement("div");
        grid.className = "ov-grid";
        group.appendChild(title);
        group.appendChild(grid);
        groupsEl.appendChild(group);
      }
      const titleEl = group.querySelector(".ov-group-title");
      if (!multiGroup && key === NO_AREA) {
        titleEl.hidden = true;
      } else {
        titleEl.hidden = false;
        titleEl.textContent = key;
      }
      return group.querySelector(".ov-grid");
    }

    _upsertTile(container, entityId, info) {
      let tile = container.querySelector(
        `.ov-tile[data-entity="${CSS.escape(entityId)}"]`
      );

      if (!info) {
        if (!tile) {
          tile = document.createElement("div");
          tile.className = "ov-tile ov-missing";
          tile.dataset.entity = entityId;
          tile.innerHTML = `<div class="ov-name"></div><div class="ov-label">Entité introuvable</div>`;
          container.appendChild(tile);
        }
        tile.querySelector(".ov-name").textContent = entityId;
        return;
      }

      const alertClass = info.isAlert ? "is-alert" : "is-ok";

      if (!tile) {
        tile = document.createElement("div");
        tile.dataset.entity = entityId;
        tile.innerHTML = `
          <div class="ov-name"></div>
          <button class="ov-visual" type="button" title="Détails">
            <img alt="" decoding="async" />
          </button>
          <div class="ov-label"></div>
          <div class="ov-controls"></div>
        `;
        container.appendChild(tile);
      }

      tile.className = `ov-tile ${alertClass}`;
      const nameEl = tile.querySelector(".ov-name");
      // La pièce est dans le titre de groupe → nom seul, bien visible
      nameEl.textContent = info.name;
      nameEl.classList.add("ov-name-only");
      tile.querySelector(".ov-label").textContent = info.label;

      const visual = tile.querySelector(".ov-visual");
      visual.setAttribute("data-more", entityId);

      const img = tile.querySelector("img");
      if (info.image && img.getAttribute("src") !== info.image) {
        img.setAttribute("src", info.image);
      }
      if (img.getAttribute("alt") !== info.label) {
        img.setAttribute("alt", info.label);
      }

      const controls = tile.querySelector(".ov-controls");
      const buttons = this._resolveControls(info, entityId);
      const nextKey = buttons.map((b) => `${b.cls}:${b.id}:${b.label}`).join("|");
      if (controls.dataset.key !== nextKey) {
        controls.dataset.key = nextKey;
        controls.innerHTML = "";
        for (const b of buttons) {
          const el = document.createElement("button");
          el.type = "button";
          el.className = `ov-btn ${b.cls}`;
          el.dataset.entity = b.id;
          el.textContent = b.label;
          controls.appendChild(el);
        }
      }
    }

    _update(force) {
      if (!this._config) return;

      const entities = this._entities();
      if (!this._hass || !entities.length) {
        if (!this._root) {
          this._root = document.createElement("ha-card");
          this.appendChild(this._root);
        }
        const title = this._config.title || "";
        const hintSig = `hint|${title}`;
        if (this._lastSig === hintSig && !force) return;
        this._lastSig = hintSig;
        this._built = false;
        this._root.innerHTML = `
          <style>${STYLES}</style>
          ${title ? `<div class="ov-title">${title}</div>` : ""}
          <div class="ov-hint">
            Choisissez un capteur <code>État</code> de l’intégration
            <strong>Gestion des ouvertures</strong>
            (ex. <code>sensor.baie_salon_etat</code>).
          </div>`;
        return;
      }

      const sig = this._signature(entities);
      if (!force && sig === this._lastSig && this._built) {
        return;
      }
      this._lastSig = sig;

      const groupsEl = this._ensureShell(this._config.title || "");
      const grouped = this._groupByArea(entities);
      const multiGroup = grouped.length > 1 || (grouped[0] && grouped[0][0] !== NO_AREA);
      const areaKeys = new Set(grouped.map(([a]) => a));

      groupsEl.querySelectorAll(".ov-group").forEach((g) => {
        if (!areaKeys.has(g.dataset.area)) g.remove();
      });

      for (const [areaName, tiles] of grouped) {
        const grid = this._ensureGroup(groupsEl, areaName, multiGroup);
        grid.className = tiles.length > 1 ? "ov-grid" : "ov-single";

        const keep = new Set(tiles.map((t) => t.entityId));
        grid.querySelectorAll(".ov-tile").forEach((tile) => {
          if (!keep.has(tile.dataset.entity)) tile.remove();
        });

        for (const { entityId, info } of tiles) {
          this._upsertTile(grid, entityId, info);
        }
        groupsEl.appendChild(grid.parentElement);
      }
    }
  }

  if (!customElements.get(CARD_TYPE)) {
    customElements.define(CARD_TYPE, OuverturesCard);
  }

  window.customCards = window.customCards || [];
  const existing = window.customCards.find((c) => c.type === CARD_TYPE);
  const cardInfo = {
    type: CARD_TYPE,
    name: "Ouvertures",
    description:
      "Baies vitrées, portes, portail, garage et piscine — visuels + commandes.",
    preview: true,
    documentationURL: "https://github.com/nicdive/HA-ouvertures",
  };
  if (existing) Object.assign(existing, cardInfo);
  else window.customCards.push(cardInfo);

  console.info(
    `%c OUVERTURES-CARD %c v${CARD_VERSION} `,
    "background:#374151;color:#fff;border-radius:4px 0 0 4px;padding:2px 6px;",
    "background:#16a34a;color:#fff;border-radius:0 4px 4px 0;padding:2px 6px;"
  );
})();
