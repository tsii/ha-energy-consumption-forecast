"""Platform setup for energy_forecast integration."""
import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import (
    CONF_ENERGY_METERS,
    CONF_EXCLUDED_ENTITIES,
    CONF_VACATION_CALENDAR,
    SENSOR_TYPES,
)
from .forecaster import EnergyForecaster
from .sensor_entity import SENSOR_CLASSES

_LOGGER = logging.getLogger(__name__)

async def setup_platform(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the platform with config entry."""
    _LOGGER.debug("Setting up Energy Forecast sensors with config: %s", config_entry.data)
    
    energy_meters = config_entry.data[CONF_ENERGY_METERS]
    excluded_entities = config_entry.data.get(CONF_EXCLUDED_ENTITIES, [])
    vacation_calendar = config_entry.data.get(CONF_VACATION_CALENDAR)

    forecaster = EnergyForecaster(hass)
    
    entities = []
    for sensor_type in SENSOR_TYPES:
        sensor_class = SENSOR_CLASSES[sensor_type]
        entities.append(
            sensor_class(
                hass,
                forecaster,
                energy_meters,
                excluded_entities,
                vacation_calendar,
                sensor_type
            )
        )
    
    async_add_entities(entities)