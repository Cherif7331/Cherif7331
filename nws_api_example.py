#!/usr/bin/env python3
"""
National Weather Service API Example Script
Philadelphia, PA Weather Data Collection

This script demonstrates how to collect weather data from the NWS API
for use in machine learning models, specifically for scanrate prediction.

Required: pip install requests
"""

import requests
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional

class NWSWeatherAPI:
    """
    National Weather Service API client for Philadelphia weather data.
    """
    
    def __init__(self, user_agent: str = "WeatherDataCollector/1.0 (example@email.com)"):
        self.base_url = "https://api.weather.gov"
        self.headers = {"User-Agent": user_agent}
        
        # Philadelphia coordinates and grid information
        self.lat = 39.9526
        self.lon = -75.1652
        self.grid_office = "PHI"
        self.grid_x = 50
        self.grid_y = 76
        self.primary_station = "KPHL"  # Philadelphia International Airport
    
    def get_current_conditions(self) -> Optional[Dict]:
        """
        Get current weather conditions from Philadelphia International Airport.
        
        Returns:
            Dict with current weather data or None if error
        """
        url = f"{self.base_url}/stations/{self.primary_station}/observations/latest"
        
        try:
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            data = response.json()
            
            # Extract key weather parameters
            props = data['properties']
            current = {
                'timestamp': props['timestamp'],
                'temperature_c': props.get('temperature', {}).get('value'),
                'dewpoint_c': props.get('dewpoint', {}).get('value'),
                'humidity_percent': props.get('relativeHumidity', {}).get('value'),
                'wind_speed_kmh': props.get('windSpeed', {}).get('value'),
                'wind_direction_deg': props.get('windDirection', {}).get('value'),
                'wind_gust_kmh': props.get('windGust', {}).get('value'),
                'pressure_pa': props.get('barometricPressure', {}).get('value'),
                'visibility_m': props.get('visibility', {}).get('value'),
                'weather_description': props.get('textDescription'),
                'heat_index_c': props.get('heatIndex', {}).get('value'),
                'wind_chill_c': props.get('windChill', {}).get('value')
            }
            
            return current
            
        except requests.RequestException as e:
            print(f"Error fetching current conditions: {e}")
            return None
    
    def get_recent_observations(self, hours_back: int = 24) -> List[Dict]:
        """
        Get recent weather observations from the past specified hours.
        
        Args:
            hours_back: Number of hours back to retrieve data
            
        Returns:
            List of observation dictionaries
        """
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(hours=hours_back)
        
        url = f"{self.base_url}/stations/{self.primary_station}/observations"
        params = {
            'start': start_time.strftime('%Y-%m-%dT%H:%M:%SZ'),
            'end': end_time.strftime('%Y-%m-%dT%H:%M:%SZ')
        }
        
        try:
            response = requests.get(url, headers=self.headers, params=params)
            response.raise_for_status()
            data = response.json()
            
            observations = []
            for feature in data['features']:
                props = feature['properties']
                obs = {
                    'timestamp': props['timestamp'],
                    'temperature_c': props.get('temperature', {}).get('value'),
                    'dewpoint_c': props.get('dewpoint', {}).get('value'),
                    'humidity_percent': props.get('relativeHumidity', {}).get('value'),
                    'wind_speed_kmh': props.get('windSpeed', {}).get('value'),
                    'wind_direction_deg': props.get('windDirection', {}).get('value'),
                    'pressure_pa': props.get('barometricPressure', {}).get('value'),
                    'precipitation_mm': props.get('precipitationLastHour', {}).get('value')
                }
                observations.append(obs)
            
            return observations
            
        except requests.RequestException as e:
            print(f"Error fetching recent observations: {e}")
            return []
    
    def get_forecast_grid_data(self) -> Optional[Dict]:
        """
        Get detailed forecast grid data with hourly parameters.
        
        Returns:
            Dict with comprehensive forecast data or None if error
        """
        url = f"{self.base_url}/gridpoints/{self.grid_office}/{self.grid_x},{self.grid_y}"
        
        try:
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            data = response.json()
            
            props = data['properties']
            
            # Extract time series data for key parameters
            forecast_data = {
                'update_time': props['updateTime'],
                'valid_times': props['validTimes'],
                'temperature': self._extract_time_series(props.get('temperature', {})),
                'dewpoint': self._extract_time_series(props.get('dewpoint', {})),
                'humidity': self._extract_time_series(props.get('relativeHumidity', {})),
                'wind_speed': self._extract_time_series(props.get('windSpeed', {})),
                'wind_direction': self._extract_time_series(props.get('windDirection', {})),
                'precipitation_probability': self._extract_time_series(props.get('probabilityOfPrecipitation', {})),
                'precipitation_amount': self._extract_time_series(props.get('quantitativePrecipitation', {})),
                'sky_cover': self._extract_time_series(props.get('skyCover', {})),
                'visibility': self._extract_time_series(props.get('visibility', {}))
            }
            
            return forecast_data
            
        except requests.RequestException as e:
            print(f"Error fetching forecast grid data: {e}")
            return None
    
    def get_hourly_forecast(self) -> Optional[List[Dict]]:
        """
        Get hourly forecast for the next 7 days.
        
        Returns:
            List of hourly forecast dictionaries or None if error
        """
        url = f"{self.base_url}/gridpoints/{self.grid_office}/{self.grid_x},{self.grid_y}/forecast/hourly"
        
        try:
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            data = response.json()
            
            hourly_data = []
            for period in data['properties']['periods']:
                forecast = {
                    'start_time': period['startTime'],
                    'end_time': period['endTime'],
                    'temperature_f': period['temperature'],
                    'temperature_unit': period['temperatureUnit'],
                    'wind_speed': period['windSpeed'],
                    'wind_direction': period['windDirection'],
                    'short_forecast': period['shortForecast'],
                    'detailed_forecast': period.get('detailedForecast', ''),
                    'precipitation_probability': period.get('probabilityOfPrecipitation', {}).get('value'),
                    'humidity': period.get('relativeHumidity', {}).get('value'),
                    'dewpoint': period.get('dewpoint', {}).get('value')
                }
                hourly_data.append(forecast)
            
            return hourly_data
            
        except requests.RequestException as e:
            print(f"Error fetching hourly forecast: {e}")
            return None
    
    def get_nearby_stations(self) -> List[Dict]:
        """
        Get list of nearby weather observation stations.
        
        Returns:
            List of station information dictionaries
        """
        url = f"{self.base_url}/gridpoints/{self.grid_office}/{self.grid_x},{self.grid_y}/stations"
        
        try:
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            data = response.json()
            
            stations = []
            for feature in data['features']:
                props = feature['properties']
                station = {
                    'id': props['stationIdentifier'],
                    'name': props['name'],
                    'distance_m': props.get('distance', {}).get('value'),
                    'coordinates': feature['geometry']['coordinates']
                }
                stations.append(station)
            
            return stations
            
        except requests.RequestException as e:
            print(f"Error fetching nearby stations: {e}")
            return []
    
    def _extract_time_series(self, data_dict: Dict) -> List[Dict]:
        """
        Extract time series values from NWS grid data format.
        
        Args:
            data_dict: Dictionary containing 'values' array with time series data
            
        Returns:
            List of time/value pairs
        """
        if not data_dict or 'values' not in data_dict:
            return []
        
        time_series = []
        for item in data_dict['values']:
            time_series.append({
                'valid_time': item['validTime'],
                'value': item['value']
            })
        
        return time_series

def main():
    """
    Example usage of the NWS Weather API client.
    """
    # Initialize the API client
    api = NWSWeatherAPI("ScanratePredictionModel/1.0 (your-email@domain.com)")
    
    print("=== National Weather Service API Example ===")
    print(f"Location: Philadelphia, PA ({api.lat}, {api.lon})")
    print(f"Primary Station: {api.primary_station}")
    print(f"Grid: {api.grid_office}/{api.grid_x},{api.grid_y}")
    print()
    
    # Get current conditions
    print("1. Current Conditions:")
    current = api.get_current_conditions()
    if current:
        print(f"   Time: {current['timestamp']}")
        print(f"   Temperature: {current['temperature_c']}°C")
        print(f"   Humidity: {current['humidity_percent']}%")
        print(f"   Wind: {current['wind_speed_kmh']} km/h from {current['wind_direction_deg']}°")
        print(f"   Pressure: {current['pressure_pa']} Pa")
        print(f"   Weather: {current['weather_description']}")
    else:
        print("   Failed to retrieve current conditions")
    print()
    
    # Get recent observations
    print("2. Recent Observations (last 12 hours):")
    recent = api.get_recent_observations(hours_back=12)
    print(f"   Retrieved {len(recent)} observations")
    if recent:
        print("   Sample (most recent 3):")
        for obs in recent[:3]:
            print(f"     {obs['timestamp']}: {obs['temperature_c']}°C, {obs['humidity_percent']}% RH")
    print()
    
    # Get forecast grid data
    print("3. Forecast Grid Data:")
    grid_data = api.get_forecast_grid_data()
    if grid_data:
        print(f"   Updated: {grid_data['update_time']}")
        print(f"   Valid period: {grid_data['valid_times']}")
        print(f"   Temperature points: {len(grid_data['temperature'])}")
        print(f"   Humidity points: {len(grid_data['humidity'])}")
        print(f"   Wind speed points: {len(grid_data['wind_speed'])}")
        
        # Show next few temperature values
        if grid_data['temperature']:
            print("   Next 3 temperature forecasts:")
            for temp in grid_data['temperature'][:3]:
                print(f"     {temp['valid_time']}: {temp['value']}°C")
    else:
        print("   Failed to retrieve forecast grid data")
    print()
    
    # Get hourly forecast
    print("4. Hourly Forecast:")
    hourly = api.get_hourly_forecast()
    if hourly:
        print(f"   Retrieved {len(hourly)} hourly periods")
        print("   Next 6 hours:")
        for period in hourly[:6]:
            print(f"     {period['start_time']}: {period['temperature_f']}°F, {period['short_forecast']}")
    else:
        print("   Failed to retrieve hourly forecast")
    print()
    
    # Get nearby stations
    print("5. Nearby Stations:")
    stations = api.get_nearby_stations()
    print(f"   Found {len(stations)} stations")
    if stations:
        print("   Closest 5 stations:")
        for station in stations[:5]:
            distance_km = station['distance_m'] / 1000 if station['distance_m'] else 0
            print(f"     {station['id']}: {station['name']} ({distance_km:.1f} km)")
    print()
    
    print("=== Data Collection Complete ===")
    print("\nFor your machine learning model, you can:")
    print("1. Collect current conditions regularly (every hour)")
    print("2. Store historical observations for training data")
    print("3. Use forecast grid data for future weather predictions")
    print("4. Combine with NCEI historical data for longer time series")

if __name__ == "__main__":
    main()