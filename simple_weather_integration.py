#!/usr/bin/env python3
"""
Simple Weather Integration - Updated with National Weather Service API
Philadelphia, PA - Scanrate Prediction Model

This script integrates comprehensive weather data collection from the National Weather Service API
for machine learning model training and real-time scanrate prediction.

Updated with complete NWS API exploration results including:
- Current conditions from KPHL (Philadelphia International Airport)
- Historical observations with date range queries
- Detailed forecast grid data with all weather parameters
- Multiple nearby weather stations
- Error handling and data validation

Required: pip install requests pandas (optional for data processing)
"""

import requests
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Union
import time

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class WeatherIntegration:
    """
    Enhanced Weather Integration class for Philadelphia scanrate prediction.
    Integrates with National Weather Service API for comprehensive weather data.
    """
    
    def __init__(self, user_agent: str = "ScanratePrediction/2.0 (weather-integration@yoursite.com)"):
        """
        Initialize the weather integration client.
        
        Args:
            user_agent: Required User-Agent header for NWS API
        """
        # NWS API Configuration
        self.base_url = "https://api.weather.gov"
        self.headers = {"User-Agent": user_agent}
        
        # Philadelphia specific configuration (from API exploration)
        self.location = {
            'name': 'Philadelphia, PA',
            'latitude': 39.9526,
            'longitude': -75.1652,
            'grid_office': 'PHI',
            'grid_x': 50,
            'grid_y': 76,
            'primary_station': 'KPHL',  # Philadelphia International Airport
            'timezone': 'America/New_York'
        }
        
        # Additional stations for data validation/backup
        self.backup_stations = ['KPNE', 'KLOM', 'KEWR', 'KBWI']
        
        # Cache for reducing API calls
        self._cache = {}
        self._cache_timeout = 300  # 5 minutes
        
        logger.info(f"Weather Integration initialized for {self.location['name']}")
        logger.info(f"Primary station: {self.location['primary_station']}")
        logger.info(f"Grid: {self.location['grid_office']}/{self.location['grid_x']},{self.location['grid_y']}")
    
    def get_current_conditions(self, station_id: str = None) -> Optional[Dict]:
        """
        Get current weather conditions optimized for scanrate prediction.
        
        Args:
            station_id: Weather station ID (defaults to KPHL)
            
        Returns:
            Dict with current weather data formatted for ML model
        """
        station = station_id or self.location['primary_station']
        cache_key = f"current_{station}"
        
        # Check cache
        if self._is_cached(cache_key):
            logger.debug(f"Returning cached current conditions for {station}")
            return self._cache[cache_key]['data']
        
        url = f"{self.base_url}/stations/{station}/observations/latest"
        
        try:
            response = requests.get(url, headers=self.headers, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            # Extract and format data for scanrate prediction model
            props = data['properties']
            
            current_conditions = {
                # Core identifiers
                'timestamp': props['timestamp'],
                'station_id': station,
                'collection_time': datetime.utcnow().isoformat(),
                
                # Temperature data (critical for scanrate)
                'temperature_c': self._safe_extract(props, 'temperature'),
                'temperature_f': self._celsius_to_fahrenheit(self._safe_extract(props, 'temperature')),
                'dewpoint_c': self._safe_extract(props, 'dewpoint'),
                'heat_index_c': self._safe_extract(props, 'heatIndex'),
                'wind_chill_c': self._safe_extract(props, 'windChill'),
                'apparent_temp_c': self._safe_extract(props, 'heatIndex') or self._safe_extract(props, 'windChill'),
                
                # Humidity (affects scanning conditions)
                'relative_humidity': self._safe_extract(props, 'relativeHumidity'),
                
                # Wind data (critical for outdoor scanning)
                'wind_speed_kmh': self._safe_extract(props, 'windSpeed'),
                'wind_speed_mph': self._kmh_to_mph(self._safe_extract(props, 'windSpeed')),
                'wind_direction_deg': self._safe_extract(props, 'windDirection'),
                'wind_direction_cardinal': self._degrees_to_cardinal(self._safe_extract(props, 'windDirection')),
                'wind_gust_kmh': self._safe_extract(props, 'windGust'),
                'wind_gust_mph': self._kmh_to_mph(self._safe_extract(props, 'windGust')),
                
                # Atmospheric pressure (affects equipment)
                'pressure_pa': self._safe_extract(props, 'barometricPressure'),
                'pressure_inhg': self._pa_to_inhg(self._safe_extract(props, 'barometricPressure')),
                'sea_level_pressure_pa': self._safe_extract(props, 'seaLevelPressure'),
                
                # Visibility and precipitation (scanning conditions)
                'visibility_m': self._safe_extract(props, 'visibility'),
                'visibility_mi': self._meters_to_miles(self._safe_extract(props, 'visibility')),
                'precipitation_1hr_mm': self._safe_extract(props, 'precipitationLastHour'),
                'precipitation_3hr_mm': self._safe_extract(props, 'precipitationLast3Hours'),
                'precipitation_6hr_mm': self._safe_extract(props, 'precipitationLast6Hours'),
                
                # Weather description
                'weather_description': props.get('textDescription', ''),
                'weather_icon': props.get('icon', ''),
                'present_weather': props.get('presentWeather', []),
                
                # Cloud conditions
                'cloud_layers': props.get('cloudLayers', []),
                
                # Data quality
                'data_quality': self._assess_data_quality(props),
                'raw_metar': props.get('rawMessage', '')
            }
            
            # Cache the result
            self._cache[cache_key] = {
                'data': current_conditions,
                'timestamp': time.time()
            }
            
            logger.info(f"Successfully retrieved current conditions from {station}")
            return current_conditions
            
        except requests.RequestException as e:
            logger.error(f"Error fetching current conditions from {station}: {e}")
            
            # Try backup station if primary fails
            if station == self.location['primary_station'] and self.backup_stations:
                logger.info("Attempting backup station...")
                for backup in self.backup_stations:
                    result = self.get_current_conditions(backup)
                    if result:
                        logger.info(f"Successfully retrieved data from backup station {backup}")
                        return result
            
            return None
    
    def get_historical_observations(self, 
                                  hours_back: int = 24, 
                                  station_id: str = None,
                                  start_date: datetime = None,
                                  end_date: datetime = None) -> List[Dict]:
        """
        Get historical weather observations for model training.
        
        Args:
            hours_back: Hours back from now (if start_date/end_date not provided)
            station_id: Weather station ID
            start_date: Custom start date
            end_date: Custom end date
            
        Returns:
            List of historical observation dictionaries
        """
        station = station_id or self.location['primary_station']
        
        # Set date range
        if start_date and end_date:
            start_time = start_date
            end_time = end_date
        else:
            end_time = datetime.utcnow()
            start_time = end_time - timedelta(hours=hours_back)
        
        url = f"{self.base_url}/stations/{station}/observations"
        params = {
            'start': start_time.strftime('%Y-%m-%dT%H:%M:%SZ'),
            'end': end_time.strftime('%Y-%m-%dT%H:%M:%SZ')
        }
        
        try:
            response = requests.get(url, headers=self.headers, params=params, timeout=15)
            response.raise_for_status()
            data = response.json()
            
            observations = []
            for feature in data['features']:
                props = feature['properties']
                
                # Format each observation similarly to current conditions
                obs = {
                    'timestamp': props['timestamp'],
                    'station_id': station,
                    'temperature_c': self._safe_extract(props, 'temperature'),
                    'dewpoint_c': self._safe_extract(props, 'dewpoint'),
                    'relative_humidity': self._safe_extract(props, 'relativeHumidity'),
                    'wind_speed_kmh': self._safe_extract(props, 'windSpeed'),
                    'wind_direction_deg': self._safe_extract(props, 'windDirection'),
                    'wind_gust_kmh': self._safe_extract(props, 'windGust'),
                    'pressure_pa': self._safe_extract(props, 'barometricPressure'),
                    'visibility_m': self._safe_extract(props, 'visibility'),
                    'precipitation_1hr_mm': self._safe_extract(props, 'precipitationLastHour'),
                    'weather_description': props.get('textDescription', ''),
                    'data_quality': self._assess_data_quality(props)
                }
                observations.append(obs)
            
            logger.info(f"Retrieved {len(observations)} historical observations from {station}")
            return observations
            
        except requests.RequestException as e:
            logger.error(f"Error fetching historical observations from {station}: {e}")
            return []
    
    def get_forecast_data(self, detailed: bool = True) -> Optional[Dict]:
        """
        Get forecast data optimized for scanrate prediction models.
        
        Args:
            detailed: If True, returns detailed grid data; if False, returns hourly forecast
            
        Returns:
            Dict with forecast data
        """
        cache_key = f"forecast_{'detailed' if detailed else 'hourly'}"
        
        # Check cache
        if self._is_cached(cache_key):
            logger.debug("Returning cached forecast data")
            return self._cache[cache_key]['data']
        
        if detailed:
            url = f"{self.base_url}/gridpoints/{self.location['grid_office']}/{self.location['grid_x']},{self.location['grid_y']}"
        else:
            url = f"{self.base_url}/gridpoints/{self.location['grid_office']}/{self.location['grid_x']},{self.location['grid_y']}/forecast/hourly"
        
        try:
            response = requests.get(url, headers=self.headers, timeout=15)
            response.raise_for_status()
            data = response.json()
            
            if detailed:
                # Process detailed grid data
                props = data['properties']
                forecast_data = {
                    'update_time': props['updateTime'],
                    'valid_times': props['validTimes'],
                    'grid_info': {
                        'office': self.location['grid_office'],
                        'grid_x': self.location['grid_x'],
                        'grid_y': self.location['grid_y']
                    },
                    # Extract time series for scanrate-relevant parameters
                    'temperature': self._extract_time_series(props.get('temperature', {})),
                    'dewpoint': self._extract_time_series(props.get('dewpoint', {})),
                    'humidity': self._extract_time_series(props.get('relativeHumidity', {})),
                    'wind_speed': self._extract_time_series(props.get('windSpeed', {})),
                    'wind_direction': self._extract_time_series(props.get('windDirection', {})),
                    'wind_gust': self._extract_time_series(props.get('windGust', {})),
                    'precipitation_probability': self._extract_time_series(props.get('probabilityOfPrecipitation', {})),
                    'precipitation_amount': self._extract_time_series(props.get('quantitativePrecipitation', {})),
                    'pressure': self._extract_time_series(props.get('pressure', {})),
                    'sky_cover': self._extract_time_series(props.get('skyCover', {})),
                    'visibility': self._extract_time_series(props.get('visibility', {})),
                    'apparent_temperature': self._extract_time_series(props.get('apparentTemperature', {}))
                }
            else:
                # Process hourly forecast data
                forecast_data = {
                    'update_time': data['properties']['updateTime'],
                    'periods': []
                }
                
                for period in data['properties']['periods']:
                    period_data = {
                        'start_time': period['startTime'],
                        'end_time': period['endTime'],
                        'temperature_f': period['temperature'],
                        'temperature_c': self._fahrenheit_to_celsius(period['temperature']),
                        'wind_speed': period['windSpeed'],
                        'wind_direction': period['windDirection'],
                        'short_forecast': period['shortForecast'],
                        'detailed_forecast': period.get('detailedForecast', ''),
                        'precipitation_probability': period.get('probabilityOfPrecipitation', {}).get('value'),
                        'humidity': period.get('relativeHumidity', {}).get('value'),
                        'dewpoint': period.get('dewpoint', {}).get('value')
                    }
                    forecast_data['periods'].append(period_data)
            
            # Cache the result
            self._cache[cache_key] = {
                'data': forecast_data,
                'timestamp': time.time()
            }
            
            logger.info(f"Successfully retrieved {'detailed' if detailed else 'hourly'} forecast data")
            return forecast_data
            
        except requests.RequestException as e:
            logger.error(f"Error fetching forecast data: {e}")
            return None
    
    def get_scanrate_optimized_data(self) -> Dict:
        """
        Get weather data specifically optimized for scanrate prediction.
        Combines current conditions and short-term forecasts.
        
        Returns:
            Dict with scanrate-optimized weather data
        """
        logger.info("Collecting scanrate-optimized weather data...")
        
        # Get current conditions
        current = self.get_current_conditions()
        
        # Get next 6 hours of detailed forecasts
        forecast = self.get_forecast_data(detailed=True)
        
        # Get recent 6 hours of observations for trend analysis
        recent = self.get_historical_observations(hours_back=6)
        
        scanrate_data = {
            'collection_timestamp': datetime.utcnow().isoformat(),
            'location': self.location,
            'current_conditions': current,
            'recent_trend': self._calculate_trends(recent),
            'forecast_next_6hrs': self._extract_next_hours(forecast, 6) if forecast else None,
            'scanrate_factors': self._calculate_scanrate_factors(current, recent, forecast),
            'data_quality_score': self._calculate_overall_quality(current, recent, forecast)
        }
        
        logger.info("Scanrate-optimized data collection complete")
        return scanrate_data
    
    def get_multiple_stations_data(self) -> Dict:
        """
        Get current conditions from multiple stations for data validation.
        
        Returns:
            Dict with data from primary and backup stations
        """
        stations_data = {}
        all_stations = [self.location['primary_station']] + self.backup_stations
        
        for station in all_stations:
            data = self.get_current_conditions(station)
            if data:
                stations_data[station] = data
                logger.info(f"Retrieved data from station {station}")
            else:
                logger.warning(f"Failed to retrieve data from station {station}")
        
        return stations_data
    
    # Helper methods for data processing and conversion
    
    def _safe_extract(self, props: Dict, key: str) -> Optional[float]:
        """Safely extract numeric value from weather properties."""
        try:
            value_dict = props.get(key, {})
            if isinstance(value_dict, dict):
                return value_dict.get('value')
            return value_dict
        except (KeyError, TypeError):
            return None
    
    def _extract_time_series(self, data_dict: Dict) -> List[Dict]:
        """Extract time series values from NWS grid data format."""
        if not data_dict or 'values' not in data_dict:
            return []
        
        time_series = []
        for item in data_dict['values']:
            time_series.append({
                'valid_time': item['validTime'],
                'value': item['value']
            })
        
        return time_series
    
    def _extract_next_hours(self, forecast_data: Dict, hours: int) -> List[Dict]:
        """Extract next N hours of forecast data."""
        if not forecast_data or 'temperature' not in forecast_data:
            return []
        
        # Take first N points from each parameter
        next_hours = []
        temp_data = forecast_data['temperature'][:hours]
        
        for i, temp in enumerate(temp_data):
            hour_data = {
                'valid_time': temp['valid_time'],
                'temperature': temp['value']
            }
            
            # Add other parameters if available
            for param in ['humidity', 'wind_speed', 'wind_direction', 'precipitation_probability']:
                if param in forecast_data and i < len(forecast_data[param]):
                    hour_data[param] = forecast_data[param][i]['value']
            
            next_hours.append(hour_data)
        
        return next_hours
    
    def _calculate_trends(self, recent_data: List[Dict]) -> Dict:
        """Calculate weather trends from recent observations."""
        if not recent_data or len(recent_data) < 2:
            return {}
        
        # Sort by timestamp
        sorted_data = sorted(recent_data, key=lambda x: x['timestamp'])
        
        trends = {}
        
        # Calculate temperature trend
        temps = [obs['temperature_c'] for obs in sorted_data if obs['temperature_c'] is not None]
        if len(temps) >= 2:
            trends['temperature_trend'] = temps[-1] - temps[0]
            trends['temperature_rate'] = trends['temperature_trend'] / len(temps)
        
        # Calculate pressure trend
        pressures = [obs['pressure_pa'] for obs in sorted_data if obs['pressure_pa'] is not None]
        if len(pressures) >= 2:
            trends['pressure_trend'] = pressures[-1] - pressures[0]
            trends['pressure_rate'] = trends['pressure_trend'] / len(pressures)
        
        # Calculate wind trend
        winds = [obs['wind_speed_kmh'] for obs in sorted_data if obs['wind_speed_kmh'] is not None]
        if len(winds) >= 2:
            trends['wind_trend'] = winds[-1] - winds[0]
            trends['wind_rate'] = trends['wind_trend'] / len(winds)
        
        return trends
    
    def _calculate_scanrate_factors(self, current: Dict, recent: List[Dict], forecast: Dict) -> Dict:
        """Calculate factors that specifically affect scanrate performance."""
        factors = {}
        
        if current:
            # Temperature factor (extreme temps affect scanning)
            temp = current.get('temperature_c')
            if temp is not None:
                if temp < 0:
                    factors['temperature_factor'] = 'very_cold'
                elif temp < 10:
                    factors['temperature_factor'] = 'cold'
                elif temp > 35:
                    factors['temperature_factor'] = 'very_hot'
                elif temp > 30:
                    factors['temperature_factor'] = 'hot'
                else:
                    factors['temperature_factor'] = 'optimal'
            
            # Wind factor (affects outdoor scanning)
            wind = current.get('wind_speed_kmh')
            if wind is not None:
                if wind > 40:
                    factors['wind_factor'] = 'very_high'
                elif wind > 25:
                    factors['wind_factor'] = 'high'
                elif wind > 15:
                    factors['wind_factor'] = 'moderate'
                else:
                    factors['wind_factor'] = 'low'
            
            # Humidity factor (affects equipment)
            humidity = current.get('relative_humidity')
            if humidity is not None:
                if humidity > 90:
                    factors['humidity_factor'] = 'very_high'
                elif humidity > 70:
                    factors['humidity_factor'] = 'high'
                elif humidity < 30:
                    factors['humidity_factor'] = 'low'
                else:
                    factors['humidity_factor'] = 'normal'
            
            # Precipitation factor
            precip = current.get('precipitation_1hr_mm')
            if precip is not None and precip > 0:
                factors['precipitation_factor'] = 'active'
            else:
                factors['precipitation_factor'] = 'none'
        
        return factors
    
    def _assess_data_quality(self, props: Dict) -> str:
        """Assess the quality of weather data."""
        quality_indicators = 0
        total_checks = 0
        
        # Check for presence of key fields
        key_fields = ['temperature', 'dewpoint', 'windSpeed', 'barometricPressure', 'relativeHumidity']
        for field in key_fields:
            total_checks += 1
            if props.get(field, {}).get('value') is not None:
                quality_indicators += 1
        
        if total_checks == 0:
            return 'unknown'
        
        quality_ratio = quality_indicators / total_checks
        
        if quality_ratio >= 0.8:
            return 'high'
        elif quality_ratio >= 0.6:
            return 'medium'
        else:
            return 'low'
    
    def _calculate_overall_quality(self, current: Dict, recent: List[Dict], forecast: Dict) -> float:
        """Calculate overall data quality score (0-1)."""
        quality_score = 0.0
        weight_sum = 0.0
        
        # Current data quality (weight: 0.5)
        if current and current.get('data_quality'):
            quality_map = {'high': 1.0, 'medium': 0.7, 'low': 0.4, 'unknown': 0.2}
            quality_score += quality_map.get(current['data_quality'], 0.2) * 0.5
            weight_sum += 0.5
        
        # Recent data availability (weight: 0.3)
        if recent:
            recent_quality = len(recent) / 6.0  # Expecting 6 hours of data
            quality_score += min(recent_quality, 1.0) * 0.3
            weight_sum += 0.3
        
        # Forecast data availability (weight: 0.2)
        if forecast:
            quality_score += 1.0 * 0.2
            weight_sum += 0.2
        
        return quality_score / weight_sum if weight_sum > 0 else 0.0
    
    def _is_cached(self, key: str) -> bool:
        """Check if data is cached and still valid."""
        if key not in self._cache:
            return False
        
        age = time.time() - self._cache[key]['timestamp']
        return age < self._cache_timeout
    
    # Unit conversion helpers
    
    def _celsius_to_fahrenheit(self, celsius: Optional[float]) -> Optional[float]:
        """Convert Celsius to Fahrenheit."""
        return (celsius * 9/5) + 32 if celsius is not None else None
    
    def _fahrenheit_to_celsius(self, fahrenheit: Optional[float]) -> Optional[float]:
        """Convert Fahrenheit to Celsius."""
        return (fahrenheit - 32) * 5/9 if fahrenheit is not None else None
    
    def _kmh_to_mph(self, kmh: Optional[float]) -> Optional[float]:
        """Convert km/h to mph."""
        return kmh * 0.621371 if kmh is not None else None
    
    def _pa_to_inhg(self, pa: Optional[float]) -> Optional[float]:
        """Convert Pascals to inches of mercury."""
        return pa * 0.0002953 if pa is not None else None
    
    def _meters_to_miles(self, meters: Optional[float]) -> Optional[float]:
        """Convert meters to miles."""
        return meters * 0.000621371 if meters is not None else None
    
    def _degrees_to_cardinal(self, degrees: Optional[float]) -> Optional[str]:
        """Convert wind direction degrees to cardinal direction."""
        if degrees is None:
            return None
        
        directions = ["N", "NNE", "NE", "ENE", "E", "ESE", "SE", "SSE",
                     "S", "SSW", "SW", "WSW", "W", "WNW", "NW", "NNW"]
        index = round(degrees / 22.5) % 16
        return directions[index]


def main():
    """
    Example usage of the enhanced Weather Integration system.
    """
    print("=== Simple Weather Integration - Enhanced for Scanrate Prediction ===")
    print("Location: Philadelphia, PA")
    print("Data Source: National Weather Service API")
    print()
    
    # Initialize the weather integration
    weather = WeatherIntegration("ScanratePrediction/2.0 (your-email@domain.com)")
    
    # Get scanrate-optimized weather data
    print("1. Collecting scanrate-optimized weather data...")
    scanrate_data = weather.get_scanrate_optimized_data()
    
    if scanrate_data['current_conditions']:
        current = scanrate_data['current_conditions']
        print(f"   Current Temperature: {current['temperature_c']:.1f}°C ({current['temperature_f']:.1f}°F)")
        print(f"   Humidity: {current['relative_humidity']:.1f}%")
        print(f"   Wind: {current['wind_speed_kmh']:.1f} km/h {current['wind_direction_cardinal']}")
        print(f"   Pressure: {current['pressure_inhg']:.2f} inHg")
        print(f"   Weather: {current['weather_description']}")
        print(f"   Data Quality: {current['data_quality']}")
    
    # Show scanrate factors
    if scanrate_data['scanrate_factors']:
        factors = scanrate_data['scanrate_factors']
        print(f"\n2. Scanrate Affecting Factors:")
        print(f"   Temperature Factor: {factors.get('temperature_factor', 'unknown')}")
        print(f"   Wind Factor: {factors.get('wind_factor', 'unknown')}")
        print(f"   Humidity Factor: {factors.get('humidity_factor', 'unknown')}")
        print(f"   Precipitation: {factors.get('precipitation_factor', 'unknown')}")
    
    # Show data quality
    print(f"\n3. Overall Data Quality Score: {scanrate_data['data_quality_score']:.2f}")
    
    # Show recent trends
    if scanrate_data['recent_trend']:
        trends = scanrate_data['recent_trend']
        print(f"\n4. Recent Weather Trends (last 6 hours):")
        if 'temperature_trend' in trends:
            print(f"   Temperature: {trends['temperature_trend']:+.1f}°C change")
        if 'pressure_trend' in trends:
            print(f"   Pressure: {trends['pressure_trend']:+.0f} Pa change")
        if 'wind_trend' in trends:
            print(f"   Wind Speed: {trends['wind_trend']:+.1f} km/h change")
    
    # Show next few hours forecast
    if scanrate_data['forecast_next_6hrs']:
        print(f"\n5. Next 6 Hours Forecast:")
        for i, hour in enumerate(scanrate_data['forecast_next_6hrs'][:3]):
            if hour.get('temperature') is not None:
                print(f"   Hour +{i+1}: {hour['temperature']:.1f}°C, "
                      f"Humidity: {hour.get('humidity', 'N/A')}%, "
                      f"Wind: {hour.get('wind_speed', 'N/A')} km/h")
    
    print(f"\n6. Multiple Stations Validation:")
    stations_data = weather.get_multiple_stations_data()
    for station_id, data in stations_data.items():
        if data:
            print(f"   {station_id}: {data['temperature_c']:.1f}°C, {data['relative_humidity']:.1f}% RH")
    
    print("\n=== Weather Integration Complete ===")
    print("\nThis enhanced integration provides:")
    print("• Real-time conditions optimized for scanrate prediction")
    print("• Weather trend analysis for pattern recognition")
    print("• Multiple station validation for data reliability")
    print("• Scanrate-specific environmental factors")
    print("• Quality assessment for model confidence")
    print("• Forecast data for predictive modeling")


if __name__ == "__main__":
    main()