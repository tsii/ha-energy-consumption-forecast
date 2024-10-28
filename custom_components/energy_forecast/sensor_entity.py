"""Energy Forecast sensor entity implementation."""
from datetime import datetime
import logging
from typing import Any, Optional

from homeassistant.components.sensor import (
    SensorEntity,
    SensorStateClass,
    SensorDeviceClass,
)
from homeassistant.core import HomeAssistant
from homeassistant.util import dt as dt_util

from .const import DOMAIN, DEFAULT_NAME
from .forecaster import EnergyForecaster

_LOGGER = logging.getLogger(__name__)

class EnergyForecastSensor(SensorEntity):
    """Energy Consumption Forecast Sensor."""

    _attr_has_entity_name = True
    _attr_name = DEFAULT_NAME
    _attr_native_unit_of_measurement = "kWh"
    _attr_device_class = SensorDeviceClass.ENERGY
    _attr_state_class = SensorStateClass.TOTAL_INCREASING
    _attr_should_poll = True

    def __init__(
        self,
        hass: HomeAssistant,
        forecaster: EnergyForecaster,
        energy_meters: list[str],
        excluded_entities: list[str],
        vacation_calendar: Optional[str],
    ) -> None:
        """Initialize the sensor."""
        self.hass = hass
        self.forecaster = forecaster
        self._energy_meters = energy_meters
        self._excluded_entities = excluded_entities
        self._vacation_calendar = vacation_calendar
        self._forecast_data = {}
        
        # Generate unique_id from the combination of energy meters
        self._attr_unique_id = f"energy_forecast_{'_'.join(sorted(energy_meters))}"
        
        # Set up device info
        self._attr_device_info = {
            "identifiers": {(DOMAIN, self._attr_unique_id)},
            "name": DEFAULT_NAME,
            "manufacturer": "bolt.new",
            "model": "Energy Forecast",
            "sw_version": "1.0.0",
        }

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return entity specific state attributes."""
        return {
            "forecast": self._forecast_data,
            "energy_meters": self._energy_meters,
            "excluded_entities": self._excluded_entities,
            "vacation_calendar": self._vacation_calendar,
        }

    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        return all(
            self.hass.states.get(meter) is not None 
            for meter in self._energy_meters
        )

    async def async_update(self) -> None:
        """Update the sensor."""
        try:
            _LOGGER.debug("Updating Energy Forecast sensor")
            now = dt_util.now()
            
            # Generate forecast data
            self._forecast_data = await self.forecaster.generate_forecast(
                now,
                self._energy_meters,
                self._excluded_entities,
                self._vacation_calendar,
            )
            
            if self._forecast_data:
                # Set the current hour's forecast as the state
                current_hour = now.replace(minute=0, second=0, microsecond=0)
                current_hour_str = current_hour.strftime("%Y-%m-%dT%H:00:00")
                self._attr_native_value = self._forecast_data.get(current_hour_str, 0)
                _LOGGER.debug("Updated forecast data: %s", self._forecast_data)
            else:
                self._attr_native_value = None
                _LOGGER.warning("No forecast data available")
                
        except Exception as err:
            self._attr_native_value = None
            _LOGGER.error("Error updating Energy Forecast sensor: %s", err)