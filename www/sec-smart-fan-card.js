const Base = window.LitElement || Object.getPrototypeOf(customElements.get("ha-panel-lovelace"));
const html = Base.prototype.html;
const css = Base.prototype.css;

class SecSmartFanCard extends Base {
  static get properties() {
    return {
      hass: {},
      _config: {},
      _lastManualPct: { state: true },
    };
  }

  setConfig(config) {
    if (!config.entity) {
      throw new Error("Bitte 'entity' setzen (fan.*)");
    }
    this._config = config;
    this._lastManualPct = 50;
  }

  get _stateObj() {
    return this.hass?.states?.[this._config.entity];
  }

  render() {
    const stateObj = this._stateObj;
    if (!stateObj) {
      return this._error("Entity nicht gefunden");
    }

    const percentage = stateObj.attributes.percentage ?? 0;
    const preset = stateObj.attributes.preset_mode || "";
    const isBoost = preset === "boost";
    const level = this._levelFromPercentage(percentage);

    return html`
      <ha-card>
        <div class="header">
          <div>
            <div class="title">${this._config.name || stateObj.attributes.friendly_name || stateObj.entity_id}</div>
            <div class="subtitle">Modus: ${preset || "manual"} • Stufe ${level}</div>
          </div>
          <div class="chips">
            <span class="chip">${percentage}%</span>
            ${isBoost ? html`<span class="chip boost">Boost</span>` : ""}
          </div>
        </div>
        <div class="levels">
          ${[1,2,3,4,5,6].map((lv) => this._levelButton(lv, level))}
        </div>
        <div class="actions">
          <mwc-button outlined @click=${() => this._toggleBoost(isBoost)}>Boost ${isBoost ? "aus" : "an"}</mwc-button>
          <mwc-button dense @click=${() => this._setPreset("schedule")}>Zeitprogramm</mwc-button>
          <mwc-button dense @click=${() => this._setPreset("sleep")}>Sleep</mwc-button>
          <mwc-button dense @click=${() => this._setPreset("humidity")}>Feuchte</mwc-button>
          <mwc-button dense @click=${() => this._setPreset("co2")}>CO₂</mwc-button>
          <mwc-button dense @click=${() => this._turnOff()}>Aus</mwc-button>
        </div>
      </ha-card>
    `;
  }

  _levelButton(lv, current) {
    const pct = this._pctForLevel(lv);
    const active = lv === current;
    return html`
      <button class="level ${active ? "active" : ""}" @click=${() => this._setLevel(lv)}>
        <span>Stufe ${lv}</span>
        <small>${pct}%</small>
      </button>
    `;
  }

  async _setLevel(level) {
    const pct = this._pctForLevel(level);
    this._lastManualPct = pct;
    await this.hass.callService("fan", "set_percentage", {
      entity_id: this._config.entity,
      percentage: pct,
    });
  }

  async _toggleBoost(isBoost) {
    if (isBoost) {
      await this._setLevel(this._levelFromPercentage(this._lastManualPct || 50));
      return;
    }
    await this._setPreset("boost");
  }

  async _setPreset(preset) {
    await this.hass.callService("fan", "set_preset_mode", {
      entity_id: this._config.entity,
      preset_mode: preset,
    });
  }

  async _turnOff() {
    await this.hass.callService("fan", "turn_off", {
      entity_id: this._config.entity,
    });
  }

  _pctForLevel(level) {
    const map = {1:16,2:33,3:50,4:67,5:83,6:100};
    return map[level] || 0;
  }

  _levelFromPercentage(pct) {
    if (pct <= 0) return 0;
    const entries = [16,33,50,67,83,100];
    let best = 1;
    let diff = 200;
    entries.forEach((val, idx) => {
      const d = Math.abs(val - pct);
      if (d < diff) {
        diff = d;
        best = idx + 1;
      }
    });
    return best;
  }

  _error(message) {
    return html`<ha-card><div class="error">${message}</div></ha-card>`;
  }

  getCardSize() {
    return 3;
  }

  static get styles() {
    return css`
      ha-card {
        padding: 12px;
      }
      .header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        gap: 12px;
      }
      .title {
        font-size: 16px;
        font-weight: 600;
      }
      .subtitle {
        font-size: 12px;
        color: var(--secondary-text-color);
      }
      .chips {
        display: flex;
        gap: 6px;
      }
      .chip {
        background: var(--chip-background-color, var(--primary-background-color));
        border: 1px solid var(--divider-color);
        border-radius: 10px;
        padding: 4px 8px;
        font-size: 12px;
      }
      .chip.boost {
        background: var(--accent-color);
        color: var(--text-primary-color, #fff);
      }
      .levels {
        margin-top: 12px;
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(90px, 1fr));
        gap: 8px;
      }
      button.level {
        width: 100%;
        border-radius: 10px;
        border: 1px solid var(--divider-color);
        padding: 10px;
        background: var(--card-background-color);
        color: inherit;
        cursor: pointer;
      }
      button.level.active {
        border: 2px solid var(--accent-color);
        box-shadow: 0 0 0 1px var(--accent-color);
      }
      button.level small {
        color: var(--secondary-text-color);
      }
      .actions {
        margin-top: 12px;
        display: flex;
        flex-wrap: wrap;
        gap: 6px;
      }
      .error {
        padding: 16px;
        color: var(--error-color);
      }
    `;
  }
}

customElements.define("sec-smart-fan-card", SecSmartFanCard);

// alias for backwards compat naming
window.customCards = window.customCards || [];
window.customCards.push({
  type: "sec-smart-fan-card",
  name: "SEC Smart Fan Card",
  description: "Stufen 1-6 und Boost/Preset Steuerung",
});
