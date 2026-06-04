from __future__ import annotations

import logging

import voluptuous as vol

from homeassistant.config_entries import ConfigFlow, ConfigFlowResult

from .api import AceDryerAPI, CannotConnect, InvalidResponse
from .const import ACE_MODELS, CONF_HOST, CONF_NUM_UNITS, CONF_UNIT_MODELS, DOMAIN

_LOGGER = logging.getLogger(__name__)

_MODEL_OPTIONS = {k: v[0] for k, v in ACE_MODELS.items()}  # {"ace": "ACE", ...}


class AceDryerConfigFlow(ConfigFlow, domain=DOMAIN):
    VERSION = 1

    def __init__(self) -> None:
        self._host: str = ""
        self._num_units: int = 1

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
