"""Constants for the Energy Consumption Forecast integration."""
DOMAIN = "energy_forecast"
CONF_ENERGY_METERS = "energy_meters"
CONF_EXCLUDED_ENTITIES = "excluded_entities"
CONF_VACATION_CALENDAR = "vacation_calendar"

DEFAULT_NAME = "Energy Consumption Forecast"

ENERGY_UNITS = ["kWh", "Wh"]"""Constants for the Energy Consumption Forecast integration."""
from typing import Final

DOMAIN: Final = "energy_forecast"
CONF_ENERGY_METERS = "energy_meters"
CONF_EXCLUDED_ENTITIES = "excluded_entities"
CONF_VACATION_CALENDAR = "vacation_calendar"

DEFAULT_NAME = "Energy Consumption Forecast"
ENERGY_UNITS = ["kWh", "Wh"]

# Sensor types
SENSOR_NEXT_HOUR = "next_hour"
SENSOR_TODAY = "today"
SENSOR_TODAY_REMAINING = "today_remaining"
SENSOR_TOMORROW = "tomorrow"
SENSOR_TODAY_TO_SUNSET = "today_to_sunset"
SENSOR_TOMORROW_TO_SUNRISE = "tomorrow_to_sunrise"

SENSOR_TYPES = [
    SENSOR_NEXT_HOUR,
    SENSOR_TODAY,
    SENSOR_TODAY_REMAINING,
    SENSOR_TOMORROW,
    SENSOR_TODAY_TO_SUNSET,
    SENSOR_TOMORROW_TO_SUNRISE,
]

ATTR_FORECAST_TIME = "forecast_time"