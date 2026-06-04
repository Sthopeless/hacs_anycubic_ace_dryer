from __future__ import annotations

import logging

import voluptuous as vol

from homeassistant.config_entries import ConfigEntry, ConfigFlow, ConfigFlowResult, OptionsFlow
from homeassistant.core import callback

from .api import AceDryerAPI, CannotConnect, InvalidResponse
from .const import (
    ACE_MODELS,
    CONF_HOST,
    CONF_NUM_UNITS,
    CONF_UNIT_MODELS,
    DEFAULT_PRESETS,
    DOMAIN,
    NUM_PRESET_SLOTS,
)

_LOGGER = logging.getLogger(__name__)

_MODEL_OPTIONS = {k: v[0] for k, v in ACE_MODELS.items()}  # {"ace": "ACE", ...}


def _validate_preset(value: str) -> str:
    """Accept empty string or 'Name:Temperature' (20–100 °C)."""
    value = value.strip()
    if not value:
        return ""
    if ":" not in value:
        raise vol.Invalid("Use format  Name:Temperature  (e.g. PLA:45)")
    name, _, temp_str = value.partition(":")
    if not name.strip():
        raise vol.Invalid("Material name cannot be empty")
    try:
        temp = int(temp_str.strip())
    except ValueError:
        raise vol.Invalid("Temperature must be a whole number")
    if not 20 <= temp <= 100:
        raise vol.Invalid("Temperature must be between 20 and 100 °C")
    return f"{name.strip()}:{temp}"


# ── Config flow (initial setup wizard) ──────────────────────────────────────

class AceDryerConfigFlow(ConfigFlow, domain=DOMAIN):
    VERSION = 1

    def __init__(self) -> None:
        self._host: str = ""
        self._num_units: int = 1

    @staticmethod
    @callback
    def async_get_options_flow(entry: ConfigEntry) -> AceDryerOptionsFlow:
        return AceDryerOptionsFlow(entry)

    # ── Step 1: IP address + connection check ────────────────────
    async def async_step_user(
        self, user_input: dict | None = None
    ) -> ConfigFlowResult:
        errors: dict[str, str] = {}

        if user_input is not None:
            host = user_input[CONF_HOST].strip().rstrip("/")
            api = AceDryerAPI(host)
            try:
                data = await api.get_mmu_machine()
                self._num_units = max(1, int(data.get("num_units", 1)))
                self._host = host
            except CannotConnect:
                errors["base"] = "cannot_connect"
            except InvalidResponse:
                errors["base"] = "invalid_response"
            except Exception:
                _LOGGER.exception("Unexpected error connecting to %s", host)
                errors["base"] = "unknown"
            finally:
                await api.close()

            if not errors:
                await self.async_set_unique_id(host)
                self._abort_if_unique_id_configured()
                return await self.async_step_models()

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({
                vol.Required(CONF_HOST, description={"suggested_value": "192.168.1.x"}): str,
            }),
            errors=errors,
        )

    # ── Step 2: model selection (one dropdown per detected unit) ─
    async def async_step_models(
        self, user_input: dict | None = None
    ) -> ConfigFlowResult:
        if user_input is not None:
            unit_models = [user_input["unit_0_model"]]
            if self._num_units > 1:
                unit_models.append(user_input.get("unit_1_model", "ace_pro"))
            return self.async_create_entry(
                title=f"ACE Dryer ({self._host})",
                data={
                    CONF_HOST: self._host,
                    CONF_NUM_UNITS: self._num_units,
                    CONF_UNIT_MODELS: unit_models,
                },
            )

        schema: dict = {
            vol.Required("unit_0_model", default="ace_pro"): vol.In(_MODEL_OPTIONS),
        }
        if self._num_units > 1:
            schema[vol.Required("unit_1_model", default="ace_pro")] = vol.In(_MODEL_OPTIONS)

        return self.async_show_form(
            step_id="models",
            data_schema=vol.Schema(schema),
            description_placeholders={"num_units": str(self._num_units)},
        )


# ── Options flow (Configure button in Integrations) ─────────────────────────

class AceDryerOptionsFlow(OptionsFlow):
    def __init__(self, entry: ConfigEntry) -> None:
        self._entry = entry

    async def async_step_init(
        self, user_input: dict | None = None
    ) -> ConfigFlowResult:
        errors: dict[str, str] = {}

        if user_input is not None:
            # Validate all non-empty slots
            validated: dict[str, str] = {}
            valid = True
            for i in range(1, NUM_PRESET_SLOTS + 1):
                key = f"preset_{i}"
                raw = user_input.get(key, "").strip()
                try:
                    validated[key] = _validate_preset(raw)
                except vol.Invalid as exc:
                    errors[key] = str(exc)
                    valid = False
            if valid:
                return self.async_create_entry(title="", data=validated)

        # Build schema with current saved values (or defaults on first run)
        schema: dict = {}
        for i in range(1, NUM_PRESET_SLOTS + 1):
            key = f"preset_{i}"
            default = self._entry.options.get(
                key,
                DEFAULT_PRESETS[i - 1] if i <= len(DEFAULT_PRESETS) else "",
            )
            schema[vol.Optional(key, default=default)] = str

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(schema),
            errors=errors,
            description_placeholders={"format_hint": "Name:Temperature  (e.g. PLA:45)"},
        )
