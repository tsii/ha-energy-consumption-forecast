"""Forecasting logic for energy consumption."""
from datetime import datetime, timedelta
import logging
from typing import Dict, List, Optional

from homeassistant.core import HomeAssistant
from homeassistant.util import dt as dt_util

from .forecast_processor import ForecastProcessor

_LOGGER = logging.getLogger(__name__)

class EnergyForecaster:
    """Class to handle energy consumption forecasting."""

    def __init__(self, hass: HomeAssistant) -> None:
        """Initialize the forecaster."""
        self.hass = hass
        self.processor = ForecastProcessor(hass)

    async def generate_forecast(
        self,
        current_time: datetime,
        energy_meters: List[str],
        excluded_entities: List[str],
        vacation_calendar: Optional[str],
    ) -> Dict[str, float]:
        """Generate hourly consumption forecast for the next 24 hours."""
        _LOGGER.debug(
            "Generating forecast for energy_meters: %s, excluded_entities: %s, vacation_calendar: %s",
            energy_meters, excluded_entities, vacation_calendar
        )
        
        # Get historical data for the past 30 days
        start_date = current_time - timedelta(days=30)
        
        # Get vacation dates if calendar is configured
        vacation_dates = set()
        if vacation_calendar:
            vacation_dates = await self.processor.get_vacation_dates(vacation_calendar)
            _LOGGER.debug("Found vacation dates: %s", vacation_dates)
        
        # Get historical statistics for all energy meters
        combined_stats = {}
        for meter in energy_meters:
            if meter not in excluded_entities:
                stats = await self.processor.get_historical_stats(
                    meter, start_date, current_time
                )
                for stat in stats:
                    start = dt_util.parse_datetime(stat["start"])
                    if start:
                        if start in combined_stats:
                            combined_stats[start] += stat["sum"]
                        else:
                            combined_stats[start] = stat["sum"]
        
        if not combined_stats:
            _LOGGER.warning("No historical statistics found for entities: %s", energy_meters)
            return {}
        
        # Process historical data
        weekday_hourly, weekend_hourly = self.processor.process_historical_data(
            combined_stats, vacation_dates
        )
        
        # Generate forecast
        forecast = self.processor.generate_hourly_forecast(
            current_time, weekday_hourly, weekend_hourly
        )
        
        _LOGGER.debug("Generated forecast: %s", forecast)
        return forecast