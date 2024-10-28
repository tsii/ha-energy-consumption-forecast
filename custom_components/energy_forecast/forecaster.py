"""Forecasting logic for energy consumption."""
from datetime import datetime, timedelta
import logging
from typing import Dict, List, Optional

from homeassistant.components.recorder import get_instance
from homeassistant.components.recorder.models import StatisticData, StatisticMetaData
from homeassistant.components.recorder.statistics import (
    get_last_statistics,
    statistics_during_period,
)
from homeassistant.core import HomeAssistant
from homeassistant.util import dt as dt_util

_LOGGER = logging.getLogger(__name__)

class EnergyForecaster:
    """Class to handle energy consumption forecasting."""

    def __init__(self, hass: HomeAssistant) -> None:
        """Initialize the forecaster."""
        self.hass = hass

    async def generate_forecast(
        self,
        current_time: datetime,
        power_meter: str,
        excluded_entities: List[str],
        vacation_calendar: str,
    ) -> Dict[str, float]:
        """Generate hourly consumption forecast for the next 24 hours."""
        _LOGGER.debug(
            "Generating forecast for power_meter: %s, excluded_entities: %s, vacation_calendar: %s",
            power_meter, excluded_entities, vacation_calendar
        )
        
        # Get historical data for the past 30 days
        start_date = current_time - timedelta(days=30)
        _LOGGER.debug("Fetching historical data from %s to %s", start_date, current_time)
        
        # Get vacation dates
        vacation_dates = await self._get_vacation_dates(vacation_calendar)
        _LOGGER.debug("Found vacation dates: %s", vacation_dates)
        
        # Get historical statistics
        stats = await self._get_historical_stats(
            power_meter,
            start_date,
            current_time,
            excluded_entities
        )
        _LOGGER.debug("Retrieved %d historical statistics entries", len(stats))
        
        if not stats:
            _LOGGER.warning("No historical statistics found for entity: %s", power_meter)
            return {}
        
        # Process historical data into hourly averages
        weekday_hourly_avg = [[] for _ in range(24)]
        weekend_hourly_avg = [[] for _ in range(24)]

        for stat in stats:
            timestamp = dt_util.parse_datetime(stat["start"])
            if timestamp.date() in vacation_dates:
                continue

            value = stat["mean"]
            hour = timestamp.hour
            
            if timestamp.weekday() < 5:  # Weekday
                weekday_hourly_avg[hour].append(value)
            else:  # Weekend
                weekend_hourly_avg[hour].append(value)

        _LOGGER.debug("Processed historical data - Weekday data points: %s", 
                     [len(x) for x in weekday_hourly_avg])
        _LOGGER.debug("Processed historical data - Weekend data points: %s", 
                     [len(x) for x in weekend_hourly_avg])

        # Generate forecast for next 24 hours
        forecast = {}
        for hour_offset in range(24):
            forecast_time = current_time + timedelta(hours=hour_offset)
            hour = forecast_time.hour
            is_weekend = forecast_time.weekday() >= 5
            
            if is_weekend:
                values = weekend_hourly_avg[hour]
            else:
                values = weekday_hourly_avg[hour]
            
            # Calculate average, default to 0 if no data
            avg_value = sum(values) / len(values) if values else 0
            
            # Format timestamp for forecast
            timestamp = forecast_time.strftime("%Y-%m-%dT%H:00:00")
            forecast[timestamp] = round(avg_value, 2)

        _LOGGER.debug("Generated forecast: %s", forecast)
        return forecast

    async def _get_vacation_dates(self, calendar_entity_id: str) -> set:
        """Get vacation dates from calendar."""
        _LOGGER.debug("Fetching vacation dates from calendar: %s", calendar_entity_id)
        calendar = self.hass.states.get(calendar_entity_id)
        vacation_dates = set()
        
        if calendar is not None and calendar.attributes.get("events"):
            _LOGGER.debug("Found calendar events: %s", calendar.attributes["events"])
            for event in calendar.attributes["events"]:
                start = dt_util.parse_datetime(event["start"])
                end = dt_util.parse_datetime(event["end"])
                
                if start and end:
                    current = start
                    while current <= end:
                        vacation_dates.add(current.date())
                        current += timedelta(days=1)
        else:
            _LOGGER.warning("Calendar %s not found or has no events", calendar_entity_id)
        
        return vacation_dates

    async def _get_historical_stats(
        self,
        power_meter: str,
        start_date: datetime,
        end_date: datetime,
        excluded_entities: List[str],
    ) -> List[StatisticData]:
        """Get historical statistics for the power meter."""
        _LOGGER.debug("Fetching statistics for %s from %s to %s", 
                     power_meter, start_date, end_date)
        
        try:
            stats = await get_instance(self.hass).async_add_executor_job(
                statistics_during_period,
                self.hass,
                start_date,
                end_date,
                {power_meter},
                "hour",
                None,
                {"mean"}
            )
            
            _LOGGER.debug("Retrieved statistics: %s", stats)
            
            # Filter out any excluded entities
            if power_meter in stats:
                return stats[power_meter]
            
            _LOGGER.warning("No statistics found for power meter: %s", power_meter)
            return []
            
        except Exception as err:
            _LOGGER.exception("Error fetching statistics: %s", err)
            return []