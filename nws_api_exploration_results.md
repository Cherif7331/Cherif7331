# National Weather Service API Exploration Results
## Philadelphia, PA Weather Data Project

**Coordinates:** 39.9526, -75.1652  
**Date:** July 22, 2025  
**Purpose:** Machine learning model for scanrate prediction

---

## API Overview

The National Weather Service API (https://api.weather.gov) provides free access to weather forecasts, current observations, and alerts. The API requires a User-Agent header but no authentication or API keys.

**Base URL:** `https://api.weather.gov`  
**Rate Limits:** Not publicly disclosed but generous for typical use (requests return error if exceeded, retry after ~5 seconds)  
**Authentication:** User-Agent header required (recommend: "YourApp/1.0 (contact@yoursite.com)")

---

## Key Endpoints for Philadelphia

### 1. Location Metadata (Starting Point)
```
GET https://api.weather.gov/points/39.9526,-75.1652
```

**Response provides:**
- Grid coordinates: PHI/50,76
- Forecast office: PHI (Philadelphia)
- Links to forecast endpoints
- Nearby observation stations
- Time zone: America/New_York

### 2. Forecast Data

#### A. 12-Hour Periods (7 days)
```
GET https://api.weather.gov/gridpoints/PHI/50,76/forecast
```
- Weather description
- High/low temperatures
- Wind speed/direction
- Precipitation probability
- Detailed forecast text

#### B. Hourly Forecasts (7 days)
```
GET https://api.weather.gov/gridpoints/PHI/50,76/forecast/hourly
```
- Hourly temperature
- Hourly wind conditions
- Hourly precipitation probability
- Weather conditions

#### C. Raw Grid Data (7 days) - **MOST COMPREHENSIVE**
```
GET https://api.weather.gov/gridpoints/PHI/50,76
```

**Available Parameters (Perfect for ML Model):**
- `temperature`: Hourly temperature (°C)
- `dewpoint`: Dewpoint temperature (°C)
- `relativeHumidity`: Relative humidity (%)
- `windSpeed`: Wind speed (km/h)
- `windDirection`: Wind direction (degrees)
- `windGust`: Wind gust speed (km/h)
- `pressure`: Atmospheric pressure
- `quantitativePrecipitation`: Precipitation amount (mm)
- `probabilityOfPrecipitation`: Precipitation probability (%)
- `apparentTemperature`: Heat index/wind chill (°C)
- `skyCover`: Cloud cover percentage (%)
- `visibility`: Visibility (m)

### 3. Current Conditions & Historical Data

#### A. Latest Observation
```
GET https://api.weather.gov/stations/KPHL/observations/latest
```

#### B. Recent Observations (Historical)
```
GET https://api.weather.gov/stations/KPHL/observations
GET https://api.weather.gov/stations/KPHL/observations?start=2025-07-21T00:00:00Z&end=2025-07-22T00:00:00Z
```

**Available from KPHL (Philadelphia International Airport):**
- Temperature (°C)
- Dewpoint (°C)
- Wind speed/direction/gusts
- Barometric pressure
- Sea level pressure
- Relative humidity
- Visibility
- Precipitation (hourly, 3-hour, 6-hour)
- Heat index
- Cloud layers

#### C. Observation Stations Near Philadelphia
```
GET https://api.weather.gov/gridpoints/PHI/50,76/stations
```

**Primary Stations:**
- **KPHL**: Philadelphia International Airport (closest, most complete data)
- **KPNE**: Northeast Philadelphia Airport
- **KLOM**: Wings Field
- **KEWR**: Newark International Airport
- **KBWI**: Baltimore/Washington International

### 4. Weather Alerts
```
GET https://api.weather.gov/alerts/active?area=PA
```

---

## Data Availability Summary

### ✅ **Available Data for ML Model:**
1. **Current Conditions** (Updated every hour or less)
   - Temperature, humidity, pressure, wind, precipitation
   - From KPHL and other nearby stations

2. **Short-term Forecasts** (Next 7 days)
   - Hourly forecasts with all required parameters
   - High temporal resolution (hourly)

3. **Recent Historical Data** (Last few days to weeks)
   - Observation station data with date range queries
   - Same parameters as current conditions

### ❌ **Limitations:**
1. **Long-term Historical Data**: NWS API primarily focuses on current and forecast data
   - For extensive historical data, use NCEI (National Centers for Environmental Information)
   - NCEI Climate Data Online: https://www.ncei.noaa.gov/cdo-web/
   - Historical Observing Metadata Repository (HOMR): https://www.ncei.noaa.gov/access/homr/

2. **Data Retention**: Observation data appears to be available for recent periods but not years of history

---

## Recommended API Usage for Your Project

### For Real-time Data Collection:
```python
# Get current conditions
current = requests.get("https://api.weather.gov/stations/KPHL/observations/latest")

# Get recent observations (last 24-48 hours)
recent = requests.get("https://api.weather.gov/stations/KPHL/observations")

# Get detailed forecast data
forecast = requests.get("https://api.weather.gov/gridpoints/PHI/50,76")
```

### For Historical Data:
- Use NCEI Climate Data Online API for historical weather data
- KPHL station historical data available through NCEI
- Can supplement NWS API current data with NCEI historical data

### Required Headers:
```python
headers = {
    'User-Agent': 'ScanratePredictor/1.0 (your-email@domain.com)'
}
```

### Data Processing Notes:
- Temperatures in Celsius (convert to Fahrenheit if needed)
- Wind speeds in km/h
- Pressure in Pascals
- Time in ISO 8601 format (UTC)
- Some values may be null (handle missing data)

---

## Alternative Data Sources for Historical Data

Since NWS API has limited historical data, consider:

1. **NCEI Climate Data Online**
   - Extensive historical weather data
   - API available: https://www.ncei.noaa.gov/cdo-web/webservices/v2
   - Requires free API token

2. **OpenWeatherMap Historical API**
   - Commercial service with historical data
   - Good for filling historical gaps

3. **Weather Underground History**
   - Historical weather data
   - May require subscription for API access

---

## Sample Response Formats

### Grid Data Response Structure:
```json
{
  "properties": {
    "temperature": {
      "uom": "wmoUnit:degC",
      "values": [
        {
          "validTime": "2025-07-22T14:00:00+00:00/PT1H",
          "value": 23.33
        }
      ]
    },
    "relativeHumidity": {
      "uom": "wmoUnit:percent", 
      "values": [...]
    }
  }
}
```

### Observation Response Structure:
```json
{
  "properties": {
    "temperature": {"value": 28.3, "unitCode": "wmoUnit:degC"},
    "dewpoint": {"value": 15.6, "unitCode": "wmoUnit:degC"},
    "windSpeed": {"value": 11.16, "unitCode": "wmoUnit:km_h-1"},
    "barometricPressure": {"value": 101860, "unitCode": "wmoUnit:Pa"},
    "relativeHumidity": {"value": 46.06, "unitCode": "wmoUnit:percent"}
  }
}
```

---

## Next Steps Recommendations

1. **Implement NWS API data collection** for real-time and recent data
2. **Set up NCEI API access** for historical data (requires free registration)
3. **Create data pipeline** that combines both sources
4. **Implement error handling** for API rate limits and outages
5. **Cache data locally** to avoid repeated API calls
6. **Monitor data quality** and handle missing values appropriately

The NWS API provides excellent current and forecast data for your machine learning model, but you'll need additional sources for comprehensive historical data.