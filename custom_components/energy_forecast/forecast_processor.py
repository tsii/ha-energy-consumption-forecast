"""Process and generate energy consumption forecasts."""
from datetime import datetime, timedelta
import logging
from typing import Dict, List, Optional, Set

from homeassistant.components.recorder import get_instance
from homeassistant.components.recorder.statistics import statistics_during_period
from homeassistant.core import HomeAssistant
from homeassistant.util import dt as dt_util

_LOGGER = logging.getLogger(__name__)

class ForecastProcessor:
    """Process historical data and generate forecasts."""

    def __init__(self, hass: HomeAssistant):
        """Initialize the forecast processor."""
        self.hass = hass

    async def get_historical_stats(
        self,
        entity_id: str,
        start_date: datetime,
        end_date: datetime,
    ) -> List[dict]:
        """Fetch historical statistics for an entity."""
        try:
            stats = await get_instance(self.hass).async_add_executor_job(
                statistics_during_period,
                self.hass,
                start_date,
                end_date,
                {entity_id},
                "hour",
                None,
                {"sum"}
            )
            
            if entity_id in stats:
                return stats[entity_id]
            
            _LOGGER.warning("No statistics found for entity: %s", entity_id)
            return []
            
        except Exception as err:
            _LOGGER.error("Error fetching statistics: %s", err)
            return []

    async def get_vacation_dates(self, calendar_entity_id: str) -> Set[datetime.date]:
        """Get vacation dates from calendar."""
        vacation_dates = set()
        calendar = self.hass.states.get(calendar_entity_id)
        
        if calendar is not None and calendar.attributes.get("events"):
            for event in calendar.attributes["events"]:
                start = dt_util.parse_datetime(event["start"])
                end = dt_util.parse_datetime(event["end"])
                
                if start and end:
                    current = start
                    while current <= end:
                        vacation_dates.add(current.date())
                        current += timedelta(days=1)
        
        return vacation_dates

    def process_historical_data(
        self,
        stats: Dict[datetime, float],
        vacation_dates: Set[datetime.date] = None
    ) -> tuple[List[List[float]], List[List[float]]]:
        """Process historical data into weekday and weekend averages."""
        weekday_hourly = [[] for _ in range(24)]
        weekend_hourly = [[] for _ in range(24)]
        
        for timestamp, value in stats.items():
            if vacation_dates and timestamp.date() in vacation_dates:
                continue
                
            hour = timestamp.hour
            if timestamp.weekday() < 5:  # Weekday
                weekday_hourly[hour].append(value)
            else:  # Weekend
                weekend_hourly[hour].append(value)
                
        return weekday_hourly, weekend_hourly

    def generate_hourly_forecast(
        self,
        current_time: datetime,
        weekday_data: List[List[float]],
        weekend_data: List[List[float]],
    ) -> Dict[str, float]:
        """Generate hourly forecast for the next 24 hours."""
        forecast = {}
        
        for hour_offset in range(24):
            forecast_time = current_time + timedelta(hours=hour_offset)
            hour = forecast_time.hour
            is_weekend = forecast_time.weekday() >= 5
            
            values = weekend_data[hour] if is_weekend else weekday_data[hour]
            avg_value = sum(values) / len(values) if values else 0
            
            timestamp = forecast_time.strftime("%Y-%m-%dT%H:00:00")
            forecast[timestamp] = round(avg_value, 2)
            
        return forecast