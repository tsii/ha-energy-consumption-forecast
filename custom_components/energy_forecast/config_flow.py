"""Config flow for Energy Consumption Forecast integration."""
from typing import Any, Dict, Optional
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_NAME
from homeassistant.core import HomeAssistant, callback
from homeassistant.data_entry_flow import FlowResult
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers import selector

from .const import (
    DOMAIN,
    CONF_POWER_METER,
    CONF_EXCLUDED_ENTITIES,
    CONF_VACATION_CALENDAR,
    DEFAULT_NAME,
)

class EnergyForecastConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Energy Consumption Forecast."""

    VERSION = 1

    async def async_step_user(
        self, user_input: Dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        errors = {}

        if user_input is not None:
            # Validate the power meter entity
            if not await self._is_valid_power_meter(user_input[CONF_POWER_METER]):
                errors[CONF_POWER_METER] = "invalid_power_meter"
            # Validate the calendar entity
            elif not await self._is_valid_calendar(user_input[CONF_VACATION_CALENDAR]):
                errors[CONF_VACATION_CALENDAR] = "invalid_calendar"
            else:
                return self.async_create_entry(
                    title=DEFAULT_NAME,
                    data=user_input,
                )

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({
                vol.Required(CONF_POWER_METER): selector.EntitySelector(
                    selector.EntitySelectorConfig(
                        domain="sensor",
                        device_class="power",
                    ),
                ),
                vol.Optional(CONF_EXCLUDED_ENTITIES, default=[]): selector.EntitySelector(
                    selector.EntitySelectorConfig(
                        domain="sensor",
                        device_class="power",
                        multiple=True,
                    ),
                ),
                vol.Required(CONF_VACATION_CALENDAR): selector.EntitySelector(
                    selector.EntitySelectorConfig(
                        domain="calendar",
                    ),
                ),
            }),
            errors=errors,
        )

    async def _is_valid_power_meter(self, entity_id: str) -> bool:
        """Check if the power meter entity is valid."""
        registry = er.async_get(self.hass)
        entity = registry.async_get(entity_id)
        if entity is None:
            return False
        return entity.domain == "sensor" and entity.device_class == "power"

    async def _is_valid_calendar(self, entity_id: str) -> bool:
        """Check if the calendar entity is valid."""
        registry = er.async_get(self.hass)
        entity = registry.async_get(entity_id)
        if entity is None:
            return False
        return entity.domain == "calendar"