# Energy Consumption Forecast for Home Assistant

[![hacs_badge](https://img.shields.io/badge/HACS-Default-41BDF5.svg)](https://github.com/hacs/integration)

This Home Assistant integration provides energy consumption forecasting based on historical data. It analyzes your past energy usage patterns, distinguishing between weekdays and weekends, while taking into account vacation periods to generate accurate hourly consumption predictions.

## Features

- 24-hour energy consumption forecast
- Separate predictions for weekdays and weekends
- Vacation period exclusion using calendar integration
- Configurable power meter source
- Option to exclude specific energy entities
- Easy configuration through Home Assistant UI

## Installation

### HACS (Recommended)

1. Open HACS in your Home Assistant instance
2. Click on "Integrations"
3. Click the three dots in the top right corner
4. Select "Custom repositories"
5. Add `https://github.com/tsii/ha-energy-forecast` and select "Integration" as the category
6. Click "Add"
7. Search for "Energy Consumption Forecast"
8. Click "Download"
9. Restart Home Assistant

### Manual Installation

1. Copy the `custom_components/energy_forecast` directory to your Home Assistant's `custom_components` directory
2. Restart Home Assistant

## Configuration

1. Go to Settings → Devices & Services
2. Click "Add Integration"
3. Search for "Energy Consumption Forecast"
4. Follow the configuration steps:
   - Select your main power meter entity
   - Optionally select entities to exclude from calculations
   - Select your vacation calendar

## Usage

After configuration, the integration will create a sensor entity with the following attributes:

- State: Current hour's forecasted consumption
- Attributes:
  - `forecast`: 24-hour forecast data
  - `power_meter`: Configured power meter entity
  - `excluded_entities`: List of excluded entities
  - `vacation_calendar`: Configured vacation calendar

The forecast data follows a similar format to the `forecast.solar` integration, providing hourly predictions in watts.

## Example Sensor Data

```yaml
state: 450.5
attributes:
  forecast:
    "2023-10-20T14:00:00": 450.5
    "2023-10-20T15:00:00": 475.2
    "2023-10-20T16:00:00": 525.8
    # ... (remaining hours)
  power_meter: sensor.home_power_consumption
  excluded_entities:
    - sensor.ev_charger_power
  vacation_calendar: calendar.vacation
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.