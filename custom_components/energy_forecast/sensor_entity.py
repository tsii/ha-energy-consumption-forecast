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
"""Energy Forecast sensor entity implementation."""
from datetime import datetime, timedelta
import logging
from typing import Any, Optional

from homeassistant.components.sensor import (
    SensorEntity,
    SensorStateClass,
    SensorDeviceClass,
)
from homeassistant.const import UnitOfEnergy
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.event import async_track_time_interval
from homeassistant.helpers.sun import get_astral_event_date
from homeassistant.util import dt as dt_util

from .const import (
    DOMAIN,
    DEFAULT_NAME,
    SENSOR_TYPES,
    ATTR_FORECAST_TIME,
)
from .forecaster import EnergyForecaster

_LOGGER = logging.getLogger(__name__)

class EnergyForecastSensorBase(SensorEntity):
    """Base class for Energy Consumption Forecast Sensors."""

    _attr_has_entity_name = True
    _attr_native_unit_of_measurement = UnitOfEnergy.KILO_WATT_HOUR
    _attr_device_class = SensorDeviceClass.ENERGY
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_should_poll = False

    def __init__(
        self,
        hass: HomeAssistant,
        forecaster: EnergyForecaster,
        energy_meters: list[str],
        excluded_entities: list[str],
        vacation_calendar: Optional[str],
        sensor_type: str,
    ) -> None:
        """Initialize the sensor."""
        self.hass = hass
        self.forecaster = forecaster
        self._energy_meters = energy_meters
        self._excluded_entities = excluded_entities
        self._vacation_calendar = vacation_calendar
        self._sensor_type = sensor_type
        self._forecast_data = {}
        
        # Set up unique ID and entity ID
        base_id = f"energy_forecast_{'_'.join(sorted(energy_meters))}"
        self._attr_unique_id = f"{base_id}_{sensor_type}"
        self.entity_id = f"sensor.energy_forecast_{sensor_type}"
        
        # Set up device info
        self._attr_device_info = {
            "identifiers": {(DOMAIN, base_id)},
            "name": DEFAULT_NAME,
            "manufacturer": "bolt.new",
            "model": "Energy Forecast",
            "sw_version": "1.0.0",
        }

        # Set up name based on sensor type
        self._attr_name = f"Energy Forecast {sensor_type.replace('_', ' ').title()}"

    async def async_added_to_hass(self) -> None:
        """Handle entity which will be added."""
        await self.async_update()
        self.async_schedule_update_ha_state(True)
        
        # Update every hour
        self.async_on_remove(
            async_track_time_interval(
                self.hass,
                self._async_update,
                timedelta(hours=1)
            )
        )

    @callback
    async def _async_update(self, _now: Optional[datetime] = None) -> None:
        """Update the sensor."""
        await self.async_update()
        self.async_write_ha_state()

    async def async_update(self) -> None:
        """Update the sensor."""
        try:
            now = dt_util.now()
            self._forecast_data = await self.forecaster.generate_forecast(
                now,
                self._energy_meters,
                self._excluded_entities,
                self._vacation_calendar,
            )
            
            if self._forecast_data:
                self._update_state(now)
            else:
                self._attr_native_value = None
                
        except Exception as err:
            self._attr_native_value = None
            _LOGGER.error("Error updating Energy Forecast sensor: %s", err)

    def _update_state(self, now: datetime) -> None:
        """Update the state based on sensor type."""
        raise NotImplementedError

    def _sum_consumption(self, start_time: datetime, end_time: datetime) -> float:
        """Sum consumption between two timestamps."""
        total = 0.0
        current = start_time
        while current < end_time:
            timestamp = current.strftime("%Y-%m-%dT%H:00:00")
            if timestamp in self._forecast_data:
                total += self._forecast_data[timestamp]
            current += timedelta(hours=1)
        return round(total, 2)

class EnergyForecastNextHour(EnergyForecastSensorBase):
    """Sensor for next hour forecast."""

    def _update_state(self, now: datetime) -> None:
        """Update state for next hour forecast."""
        next_hour = (now + timedelta(hours=1)).replace(minute=0, second=0, microsecond=0)
        timestamp = next_hour.strftime("%Y-%m-%dT%H:00:00")
        self._attr_native_value = self._forecast_data.get(timestamp)
        self._attr_extra_state_attributes = {
            ATTR_FORECAST_TIME: timestamp
        }

class EnergyForecastToday(EnergyForecastSensorBase):
    """Sensor for today's total forecast."""

    def _update_state(self, now: datetime) -> None:
        """Update state for today's forecast."""
        start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        end = start + timedelta(days=1)
        self._attr_native_value = self._sum_consumption(start, end)
        self._attr_extra_state_attributes = {
            ATTR_FORECAST_TIME: start.strftime("%Y-%m-%dT%H:00:00")
        }

class EnergyForecastTodayRemaining(EnergyForecastSensorBase):
    """Sensor for remaining consumption today."""

    def _update_state(self, now: datetime) -> None:
        """Update state for remaining consumption today."""
        start = now.replace(minute=0, second=0, microsecond=0)
        end = now.replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=1)
        self._attr_native_value = self._sum_consumption(start, end)
        self._attr_extra_state_attributes = {
            ATTR_FORECAST_TIME: start.strftime("%Y-%m-%dT%H:00:00")
        }

class EnergyForecastTomorrow(EnergyForecastSensorBase):
    """Sensor for tomorrow's forecast."""

    def _update_state(self, now: datetime) -> None:
        """Update state for tomorrow's forecast."""
        start = now.replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=1)
        end = start + timedelta(days=1)
        self._attr_native_value = self._sum_consumption(start, end)
        self._attr_extra_state_attributes = {
            ATTR_FORECAST_TIME: start.strftime("%Y-%m-%dT%H:00:00")
        }

class EnergyForecastTodayToSunset(EnergyForecastSensorBase):
    """Sensor for consumption until sunset today."""

    def _update_state(self, now: datetime) -> None:
        """Update state for consumption until sunset."""
        start = now.replace(minute=0, second=0, microsecond=0)
        sunset = get_astral_event_date(self.hass, "sunset", now.date())
        if sunset and sunset > start:
            self._attr_native_value = self._sum_consumption(start, sunset)
            self._attr_extra_state_attributes = {
                ATTR_FORECAST_TIME: start.strftime("%Y-%m-%dT%H:00:00")
            }
        else:
            self._attr_native_value = 0

class EnergyForecastTomorrowToSunrise(EnergyForecastSensorBase):
    """Sensor for consumption until sunrise tomorrow."""

    def _update_state(self, now: datetime) -> None:
        """Update state for consumption until sunrise tomorrow."""
        tomorrow = now.date() + timedelta(days=1)
        start = now.replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=1)
        sunrise = get_astral_event_date(self.hass, "sunrise", tomorrow)
        if sunrise and sunrise > start:
            self._attr_native_value = self._sum_consumption(start, sunrise)
            self._attr_extra_state_attributes = {
                ATTR_FORECAST_TIME: start.strftime("%Y-%m-%dT%H:00:00")
            }
        else:
            self._attr_native_value = 0

SENSOR_CLASSES = {
    "next_hour": EnergyForecastNextHour,
    "today": EnergyForecastToday,
    "today_remaining": EnergyForecastTodayRemaining,
    "tomorrow": EnergyForecastTomorrow,
    "today_to_sunset": EnergyForecastTodayToSunset,
    "tomorrow_to_sunrise": EnergyForecastTomorrowToSunrise,
}
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