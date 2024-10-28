"""Sensor platform for energy_forecast integration."""
from datetime import datetime, timedelta
import logging
from typing import Any, Optional

from homeassistant.components.recorder import get_instance
from homeassistant.components.sensor import (
    SensorEntity,
    SensorStateClass,
    SensorDeviceClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import StateType
from homeassistant.util import dt as dt_util

from .const import (
    DOMAIN,
    CONF_POWER_METER,
    CONF_EXCLUDED_ENTITIES,
    CONF_VACATION_CALENDAR,
)
from .forecaster import EnergyForecaster

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the Energy Consumption Forecast sensor."""
    _LOGGER.debug("Setting up Energy Forecast sensor with config: %s", config_entry.data)
    
    power_meter = config_entry.data[CONF_POWER_METER]
    excluded_entities = config_entry.data.get(CONF_EXCLUDED_ENTITIES, [])
    vacation_calendar = config_entry.data[CONF_VACATION_CALENDAR]

    forecaster = EnergyForecaster(hass)
    
    async_add_entities([
        EnergyForecastSensor(
            hass, 
            forecaster,
            power_meter, 
            excluded_entities, 
            vacation_calendar
        )
    ])

class EnergyForecastSensor(SensorEntity):
    """Energy Consumption Forecast Sensor."""

    _attr_native_unit_of_measurement = "W"
    _attr_device_class = SensorDeviceClass.POWER
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_should_poll = True

    def __init__(
        self,
        hass: HomeAssistant,
        forecaster: EnergyForecaster,
        power_meter: str,
        excluded_entities: list[str],
        vacation_calendar: str,
    ) -> None:
        """Initialize the sensor."""
        _LOGGER.debug("Initializing Energy Forecast sensor with power_meter: %s", power_meter)
        self.hass = hass
        self.forecaster = forecaster
        self._power_meter = power_meter
        self._excluded_entities = excluded_entities
        self._vacation_calendar = vacation_calendar
        self._attr_name = "Energy Consumption Forecast"
        self._attr_unique_id = f"energy_forecast_{power_meter}"
        self._forecast_data = {}

    @property
    def extra_state_attributes(self):
        """Return the state attributes."""
        return {
            "forecast": self._forecast_data,
            "power_meter": self._power_meter,
            "excluded_entities": self._excluded_entities,
            "vacation_calendar": self._vacation_calendar,
        }

    async def async_update(self) -> None:
        """Update the sensor."""
        try:
            _LOGGER.debug("Updating Energy Forecast sensor")
            now = dt_util.now()
            self._forecast_data = await self.forecaster.generate_forecast(
                now,
                self._power_meter,
                self._excluded_entities,
                self._vacation_calendar,
            )
            
            # Set the current hour's forecast as the state
            current_hour = now.strftime("%Y-%m-%dT%H:00:00")
            self._attr_native_value = self._forecast_data.get(current_hour, 0)
            _LOGGER.debug("Updated forecast data: %s", self._forecast_data)
        except Exception as err:
            _LOGGER.exception("Error updating Energy Forecast sensor: %s", err)