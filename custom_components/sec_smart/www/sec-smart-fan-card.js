const Base = window.LitElement || Object.getPrototypeOf(customElements.get("ha-panel-lovelace"));
const html = Base.prototype.html;
const css = Base.prototype.css;

const STAGE_PERCENTAGES = { 1: 16, 2: 33, 3: 50, 4: 67, 5: 83, 6: 100 };

class SecSmartFanCard extends Base {
  static get properties() {
    return {
      hass: {},
      _config: {},
    };
  }

  setConfig(config) {
    if (!config.entity) {
      throw new Error("Bitte 'entity' setzen (fan.*)");
    }
    this._config = config;
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
    const stage = isBoost ? null : this._stageFromPercentage(percentage);
    const title = this._config.name
      || stateObj.attributes.friendly_name
      || stateObj.entity_id;
    const status = isBoost
      ? "Boost aktiv"
      : stage === 0
        ? "Aus"
        : `Stufe ${stage}`;
    const statusClass = isBoost ? "boost" : stage === 0 ? "off" : "on";

    return html`
      <ha-card>
        <div class="header">
          <div class="title">${title}</div>
          <div class="status ${statusClass}">${status}</div>
        </div>
        <div class="stages">
          ${[0, 1, 2, 3, 4, 5, 6].map((s) => this._stageButton(s, stage))}
        </div>
        <button
          class="boost ${isBoost ? "active" : ""}"
          @click=${() => this._toggleBoost(isBoost)}
        >
          <ha-icon icon="mdi:weather-windy"></ha-icon>
          <span>Boost lüften${isBoost ? " (aktiv)" : ""}</span>
        </button>
      </ha-card>
    `;
  }

  _stageButton(s, current) {
    const active = s === current;
    const classes = ["stage"];
    if (active) classes.push("active");
    if (s === 0) classes.push("off");
    return html`
      <button
        class=${classes.join(" ")}
        @click=${() => this._setStage(s)}
        aria-label="Stufe ${s}"
      >${s}</button>
    `;
  }

  async _setStage(stage) {
    const pct = stage === 0 ? 0 : STAGE_PERCENTAGES[stage];
    await this.hass.callService("fan", "set_percentage", {
      entity_id: this._config.entity,
      percentage: pct,
    });
  }

  async _toggleBoost(isBoost) {
    if (isBoost) {
      await this._setStage(0);
      return;
    }
    await this.hass.callService("fan", "set_preset_mode", {
      entity_id: this._config.entity,
      preset_mode: "boost",
    });
  }

  _stageFromPercentage(pct) {
    if (pct <= 0) return 0;
    let best = 1;
    let diff = 200;
    for (const [stage, val] of Object.entries(STAGE_PERCENTAGES)) {
      const d = Math.abs(val - pct);
      if (d < diff) {
        diff = d;
        best = Number(stage);
      }
    }
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
        padding: 16px;
      }
      .header {
        display: flex;
        justify-content: space-between;
        align-items: baseline;
        gap: 12px;
        margin-bottom: 16px;
      }
      .title {
        font-size: 18px;
        font-weight: 600;
        color: var(--primary-text-color);
      }
      .status {
        font-size: 13px;
        font-weight: 500;
        padding: 3px 10px;
        border-radius: 999px;
        background: var(--secondary-background-color);
        color: var(--secondary-text-color);
      }
      .status.on {
        background: rgba(var(--rgb-primary-color, 33, 150, 243), 0.15);
        color: var(--primary-color);
      }
      .status.boost {
        background: var(--accent-color);
        color: var(--text-primary-color, #fff);
      }
      .stages {
        display: grid;
        grid-template-columns: repeat(7, 1fr);
        gap: 6px;
        margin-bottom: 14px;
      }
      button.stage {
        aspect-ratio: 1 / 1;
        border-radius: 12px;
        border: 1px solid var(--divider-color);
        background: var(--card-background-color);
        color: var(--primary-text-color);
        font-size: 17px;
        font-weight: 600;
        cursor: pointer;
        font-family: inherit;
        transition: background 0.15s ease, color 0.15s ease, border-color 0.15s ease, transform 0.05s ease;
      }
      button.stage:hover {
        background: var(--secondary-background-color);
      }
      button.stage:active {
        transform: scale(0.96);
      }
      button.stage.active {
        background: var(--primary-color);
        color: var(--text-primary-color, #fff);
        border-color: var(--primary-color);
      }
      button.stage.off.active {
        background: var(--state-inactive-color, var(--disabled-color, #888));
        border-color: var(--state-inactive-color, var(--disabled-color, #888));
        color: var(--text-primary-color, #fff);
      }
      button.boost {
        width: 100%;
        padding: 12px 16px;
        border-radius: 12px;
        border: 1px solid var(--accent-color);
        background: transparent;
        color: var(--accent-color);
        font-size: 15px;
        font-weight: 600;
        cursor: pointer;
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 8px;
        font-family: inherit;
        transition: background 0.15s ease, color 0.15s ease, transform 0.05s ease;
      }
      button.boost:hover {
        background: rgba(var(--rgb-accent-color, 255, 145, 0), 0.08);
      }
      button.boost:active {
        transform: scale(0.98);
      }
      button.boost.active {
        background: var(--accent-color);
        color: var(--text-primary-color, #fff);
      }
      button.boost ha-icon {
        --mdc-icon-size: 20px;
      }
      .error {
        padding: 16px;
        color: var(--error-color);
      }
    `;
  }
}

customElements.define("sec-smart-fan-card", SecSmartFanCard);

window.customCards = window.customCards || [];
window.customCards.push({
  type: "sec-smart-fan-card",
  name: "SEC Smart Fan Card",
  description: "Stufen 0\u20136 und Boost-L\u00fcftung f\u00fcr SEC Smart",
});
