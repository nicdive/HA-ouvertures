/**
 * custom:ouvertures-card — carte visuelle Gestion des ouvertures
 * Affiche le SVG d'état et les boutons de commande selon le type.
 */
(() => {
  const CARD_VERSION = "1.1.0";
  const CARD_TYPE = "ouvertures-card";

  const OPEN_TYPES_WITH_CONTROLS = new Set([
    "portail_coulissant",
    "garage_sectionnelle",
  ]);

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

    _valueChanged(ev) {
      if (!this._config || !this._hass) return;
      const target = ev.target;
      const newConfig = { ...this._config };
      if (target.configValue) {
        if (target.value === "" && target.configValue !== "title") {
          delete newConfig[target.configValue];
        } else {
          newConfig[target.configValue] = target.value;
        }
      }
      fireEvent(this, "config-changed", { config: newConfig });
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
        el.addEventListener("change", (ev) => {
          // fallback
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
    static getStubConfig(hass, entities) {
      // Préremplit avec le premier sensor d'état ouvertures si possible
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
      // Ne pas throw si entity vide : sinon la carte n'apparaît pas
      // dans le sélecteur Lovelace (stub config).
      if (!config || typeof config !== "object") {
        throw new Error("Configuration invalide");
      }
      this._config = { ...config };
      if (this._hass) this._update();
    }

    set hass(hass) {
      this._hass = hass;
      this._update();
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
      return {
        state: st.state,
        name: st.attributes.name || st.attributes.friendly_name || entityId,
        label: st.attributes.label || st.attributes.friendly_state || st.state,
        image: st.attributes.image,
        isAlert: Boolean(st.attributes.is_alert),
        isOpen: Boolean(st.attributes.is_open),
        openingType: st.attributes.opening_type,
        openEntity: st.attributes.open_entity,
        closeEntity: st.attributes.close_entity,
        impulseEntity: st.attributes.impulse_entity,
        typeLabel: st.attributes.type_label,
      };
    }

    _findButton(deviceName, keywords) {
      // Cherche un button.ouvertures lié par nom si attributs absents
      if (!this._hass) return null;
      const lower = (deviceName || "").toLowerCase();
      for (const [id, st] of Object.entries(this._hass.states)) {
        if (!id.startsWith("button.")) continue;
        const fn = (st.attributes.friendly_name || "").toLowerCase();
        if (lower && fn.includes(lower.replace(/\s+état$/, "").trim())) {
          if (keywords.some((k) => fn.includes(k) || id.includes(k))) {
            return id;
          }
        }
      }
      return null;
    }

    async _callButton(entityId) {
      if (!entityId || !this._hass) return;
      const domain = entityId.split(".")[0];
      if (domain === "button") {
        await this._hass.callService("button", "press", { entity_id: entityId });
      } else if (domain === "input_button") {
        await this._hass.callService("input_button", "press", { entity_id: entityId });
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

    _controlsHtml(info, entityId) {
      if (!OPEN_TYPES_WITH_CONTROLS.has(info.openingType)) return "";

      const openId =
        info.openEntity ||
        this._findButton(info.name, ["ouvrir", "open"]);
      const closeId =
        info.closeEntity ||
        this._findButton(info.name, ["fermer", "close"]);
      const impulseId =
        info.impulseEntity ||
        this._findButton(info.name, ["impulsion", "impulse", "pulse"]);

      // Resolve sibling button entities from same device via unique naming
      // Prefer attributes from sensor; also look up button.*_ouvrir etc.
      const base = entityId.replace(/_etat$/, "").replace(/^sensor\./, "");
      const guess = (suffix) => {
        const candidates = [
          `button.${base}_${suffix}`,
          `button.ouvertures_${base}_${suffix}`,
        ];
        for (const c of candidates) {
          if (this._hass.states[c]) return c;
        }
        // scan
        for (const id of Object.keys(this._hass.states)) {
          if (id.startsWith("button.") && id.includes(suffix) && id.includes(base.split("_").slice(-2).join("_"))) {
            return id;
          }
        }
        return null;
      };

      const openBtn = openId || guess("ouvrir");
      const closeBtn = closeId || guess("fermer");
      const impulseBtn = impulseId || guess("impulsion");

      const buttons = [];
      if (info.openingType === "portail_coulissant") {
        if (openBtn) {
          buttons.push(
            `<button class="ov-btn ov-open" data-entity="${openBtn}">Ouvrir</button>`
          );
        }
        if (closeBtn) {
          buttons.push(
            `<button class="ov-btn ov-close" data-entity="${closeBtn}">Fermer</button>`
          );
        }
      }
      if (impulseBtn) {
        buttons.push(
          `<button class="ov-btn ov-impulse" data-entity="${impulseBtn}">Impulsion</button>`
        );
      }
      if (!buttons.length) return "";
      return `<div class="ov-controls">${buttons.join("")}</div>`;
    }

    _tile(entityId) {
      const info = this._attrs(entityId);
      if (!info) {
        return `
          <div class="ov-tile ov-missing">
            <div class="ov-name">${entityId}</div>
            <div class="ov-label">Entité introuvable</div>
          </div>`;
      }
      const alertClass = info.isAlert ? "is-alert" : "is-ok";
      return `
        <div class="ov-tile ${alertClass}" data-entity="${entityId}">
          <div class="ov-name">${info.name}</div>
          <button class="ov-visual" data-more="${entityId}" title="Détails">
            <img src="${info.image || ""}" alt="${info.label}" loading="lazy" />
          </button>
          <div class="ov-label">${info.label}</div>
          ${this._controlsHtml(info, entityId)}
        </div>`;
    }

    _update() {
      if (!this._config) return;

      if (!this._root) {
        this._root = document.createElement("ha-card");
        this.appendChild(this._root);
        this._root.addEventListener("click", (ev) => {
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
        });
      }

      const entities = this._entities();
      if (!this._hass || !entities.length) {
        const title = this._config.title
          ? `<div class="ov-title">${this._config.title}</div>`
          : "";
        this._root.innerHTML = `
          <style>
            ha-card { padding: 16px; }
            .ov-title { font-weight: 700; margin-bottom: 8px; }
            .ov-hint { color: #6b7280; font-size: 0.9rem; }
          </style>
          ${title}
          <div class="ov-hint">
            Choisissez un capteur <code>État</code> de l’intégration
            <strong>Gestion des ouvertures</strong>
            (ex. <code>sensor.baie_salon_etat</code>).
          </div>`;
        return;
      }

      const grid = entities.length > 1;
      const title = this._config.title
        ? `<div class="ov-title">${this._config.title}</div>`
        : "";

      this._root.innerHTML = `
        <style>
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
            transition: box-shadow 0.2s ease, transform 0.2s ease, border-color 0.2s ease;
          }
          .ov-tile:hover {
            transform: translateY(-2px);
            box-shadow: 0 8px 20px rgba(15, 23, 42, 0.08);
          }
          .ov-tile.is-alert {
            border-color: rgba(234, 88, 12, 0.55);
            background: rgba(255, 247, 237, 0.9);
          }
          .ov-tile.is-ok {
            border-color: rgba(22, 163, 74, 0.35);
          }
          .ov-name {
            font-weight: 650;
            font-size: 0.95rem;
            color: #111827;
            text-align: center;
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
          @media (max-width: 500px) {
            .ov-grid { grid-template-columns: 1fr 1fr; gap: 8px; }
            .ov-name { font-size: 0.85rem; }
            .ov-btn { padding: 6px 8px; font-size: 0.72rem; }
          }
        </style>
        ${title}
        <div class="${grid ? "ov-grid" : "ov-single"}">
          ${entities.map((e) => this._tile(e)).join("")}
        </div>
      `;
    }

    get hass() {
      return this._hass;
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
  if (existing) {
    Object.assign(existing, cardInfo);
  } else {
    window.customCards.push(cardInfo);
  }

  // Signale au sélecteur de cartes qu’une nouvelle carte custom est dispo
  window.dispatchEvent(new Event("ll-rebuild"));
  customElements.whenDefined("hui-card-element-editor").then(() => {
    window.dispatchEvent(new Event("ll-rebuild"));
  });

  console.info(
    `%c OUVERTURES-CARD %c v${CARD_VERSION} `,
    "background:#374151;color:#fff;border-radius:4px 0 0 4px;padding:2px 6px;",
    "background:#16a34a;color:#fff;border-radius:0 4px 4px 0;padding:2px 6px;"
  );
})();
