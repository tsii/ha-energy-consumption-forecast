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
    CONF_ENERGY_METERS,
    CONF_EXCLUDED_ENTITIES,
    CONF_VACATION_CALENDAR,
    DEFAULT_NAME,
    ENERGY_UNITS,
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
            # Validate that at least one energy meter is selected
            if not user_input.get(CONF_ENERGY_METERS):
                errors[CONF_ENERGY_METERS] = "no_energy_meters"
            # Validate all selected energy meters
            elif not await self._are_valid_energy_meters(user_input[CONF_ENERGY_METERS]):
                errors[CONF_ENERGY_METERS] = "invalid_energy_meters"
            # Validate excluded entities if provided
            elif user_input.get(CONF_EXCLUDED_ENTITIES) and not await self._are_valid_energy_meters(user_input[CONF_EXCLUDED_ENTITIES]):
                errors[CONF_EXCLUDED_ENTITIES] = "invalid_excluded_entities"
            # Validate the calendar entity if provided
            elif user_input.get(CONF_VACATION_CALENDAR) and not await self._is_valid_calendar(user_input[CONF_VACATION_CALENDAR]):
                errors[CONF_VACATION_CALENDAR] = "invalid_calendar"
            else:
                return self.async_create_entry(
                    title=DEFAULT_NAME,
                    data=user_input,
                )

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({
                vol.Required(CONF_ENERGY_METERS): selector.EntitySelector(
                    selector.EntitySelectorConfig(
                        domain="sensor",
                        device_class="energy",
                        multiple=True,
                    ),
                ),
                vol.Optional(CONF_EXCLUDED_ENTITIES, default=[]): selector.EntitySelector(
                    selector.EntitySelectorConfig(
                        domain="sensor",
                        device_class="energy",
                        multiple=True,
                    ),
                ),
                vol.Optional(CONF_VACATION_CALENDAR): selector.EntitySelector(
                    selector.EntitySelectorConfig(
                        domain="calendar",
                    ),
                ),
            }),
            errors=errors,
        )

    async def _are_valid_energy_meters(self, entity_ids: list[str]) -> bool:
        """Check if all energy meter entities are valid."""
        registry = er.async_get(self.hass)
        for entity_id in entity_ids:
            entity = registry.async_get(entity_id)
            if entity is None:
                return False
            if entity.domain != "sensor" or entity.device_class != "energy":
                return False
            state = self.hass.states.get(entity_id)
            if state is None:
                return False
            # Check if the unit is a valid energy unit
            unit = state.attributes.get("unit_of_measurement")
            if unit not in ENERGY_UNITS:
                return False
        return True

    async def _is_valid_calendar(self, entity_id: str) -> bool:
        """Check if the calendar entity is valid."""
        if not entity_id:
            return True
        registry = er.async_get(self.hass)
        entity = registry.async_get(entity_id)
        if entity is None:
            return False
        return entity.domain == "calendar"