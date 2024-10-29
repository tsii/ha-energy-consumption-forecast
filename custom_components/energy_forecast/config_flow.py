"""Config flow for Energy Consumption Forecast integration."""
from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import HomeAssistant, callback
from homeassistant.data_entry_flow import FlowResult
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers import selector
from homeassistant.helpers.entity_registry import async_get

from .const import (
    DOMAIN,
    CONF_ENERGY_METERS,
    CONF_EXCLUDED_ENTITIES,
    CONF_VACATION_CALENDAR,
    DEFAULT_NAME,
    ENERGY_UNITS,
)

_LOGGER = logging.getLogger(__name__)

async def _validate_energy_meters(hass: HomeAssistant, entity_ids: list[str]) -> bool:
    """Validate energy meter entities."""
    for entity_id in entity_ids:
        state = hass.states.get(entity_id)
        if not state:
            _LOGGER.debug("Entity %s not found", entity_id)
            return False
            
        attributes = state.attributes
        if "unit_of_measurement" not in attributes:
            _LOGGER.debug("Entity %s has no unit of measurement", entity_id)
            return False
            
        unit = attributes.get("unit_of_measurement")
        if unit not in ENERGY_UNITS:
            _LOGGER.debug("Entity %s has invalid unit: %s", entity_id, unit)
            return False
            
        device_class = attributes.get("device_class")
        if device_class and device_class != "energy":
            _LOGGER.debug("Entity %s has wrong device class: %s", entity_id, device_class)
            return False
            
    return True

async def _validate_calendar(hass: HomeAssistant, entity_id: str | None) -> bool:
    """Validate calendar entity."""
    if not entity_id:
        return True
    state = hass.states.get(entity_id)
    if not state:
        return False
    domain = entity_id.split('.')[0]
    return domain == "calendar"

class EnergyForecastConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Energy Consumption Forecast."""

    VERSION = 1

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> config_entries.OptionsFlow:
        """Get the options flow for this handler."""
        return EnergyForecastOptionsFlow(config_entry)

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        errors = {}

        if user_input is not None:
            # Validate inputs
            if not user_input.get(CONF_ENERGY_METERS):
                errors[CONF_ENERGY_METERS] = "no_energy_meters"
            elif not await _validate_energy_meters(self.hass, user_input[CONF_ENERGY_METERS]):
                errors[CONF_ENERGY_METERS] = "invalid_energy_meters"
            elif (
                user_input.get(CONF_EXCLUDED_ENTITIES)
                and not await _validate_energy_meters(self.hass, user_input[CONF_EXCLUDED_ENTITIES])
            ):
                errors[CONF_EXCLUDED_ENTITIES] = "invalid_excluded_entities"
            elif (
                user_input.get(CONF_VACATION_CALENDAR)
                and not await _validate_calendar(self.hass, user_input[CONF_VACATION_CALENDAR])
            ):
                errors[CONF_VACATION_CALENDAR] = "invalid_calendar"
            else:
                # Check if already configured
                await self.async_set_unique_id(
                    f"energy_forecast_{'_'.join(sorted(user_input[CONF_ENERGY_METERS]))}"
                )
                self._abort_if_unique_id_configured()

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

class EnergyForecastOptionsFlow(config_entries.OptionsFlow):
    """Handle options."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        """Initialize options flow."""
        self.config_entry = config_entry

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Manage the options."""
        errors = {}

        if user_input is not None:
            # Validate inputs
            if not user_input.get(CONF_ENERGY_METERS):
                errors[CONF_ENERGY_METERS] = "no_energy_meters"
            elif not await _validate_energy_meters(self.hass, user_input[CONF_ENERGY_METERS]):
                errors[CONF_ENERGY_METERS] = "invalid_energy_meters"
            elif (
                user_input.get(CONF_EXCLUDED_ENTITIES)
                and not await _validate_energy_meters(self.hass, user_input[CONF_EXCLUDED_ENTITIES])
            ):
                errors[CONF_EXCLUDED_ENTITIES] = "invalid_excluded_entities"
            elif (
                user_input.get(CONF_VACATION_CALENDAR)
                and not await _validate_calendar(self.hass, user_input[CONF_VACATION_CALENDAR])
            ):
                errors[CONF_VACATION_CALENDAR] = "invalid_calendar"
            else:
                return self.async_create_entry(title="", data=user_input)

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema({
                vol.Required(
                    CONF_ENERGY_METERS,
                    default=self.config_entry.data.get(CONF_ENERGY_METERS, []),
                ): selector.EntitySelector(
                    selector.EntitySelectorConfig(
                        domain="sensor",
                        device_class="energy",
                        multiple=True,
                    ),
                ),
                vol.Optional(
                    CONF_EXCLUDED_ENTITIES,
                    default=self.config_entry.data.get(CONF_EXCLUDED_ENTITIES, []),
                ): selector.EntitySelector(
                    selector.EntitySelectorConfig(
                        domain="sensor",
                        device_class="energy",
                        multiple=True,
                    ),
                ),
                vol.Optional(
                    CONF_VACATION_CALENDAR,
                    default=self.config_entry.data.get(CONF_VACATION_CALENDAR),
                ): selector.EntitySelector(
                    selector.EntitySelectorConfig(
                        domain="calendar",
                    ),
                ),
            }),
            errors=errors,
        )