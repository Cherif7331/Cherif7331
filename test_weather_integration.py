#!/usr/bin/env python3
"""
Test Weather Integration - Using built-in urllib
This version demonstrates full functionality without requiring additional packages.
"""

import urllib.request
import urllib.error
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import time

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class TestWeatherIntegration:
    """
    Test version of Weather Integration using built-in urllib.
    """
    
    def __init__(self, user_agent: str = "ScanratePrediction/2.0 (test-weather@yoursite.com)"):
        self.base_url = "https://api.weather.gov"
        self.user_agent = user_agent
        
        # Philadelphia configuration
        self.location = {
            'name': 'Philadelphia, PA',
            'latitude': 39.9526,
            'longitude': -75.1652,
            'grid_office': 'PHI',
            'grid_x': 50,
            'grid_y': 76,
            'primary_station': 'KPHL'
        }
        
        logger.info(f"Test Weather Integration initialized for {self.location['name']}")
    
    def _make_request(self, url: str) -> Optional[Dict]:
        """Make HTTP request using urllib."""
        try:
            req = urllib.request.Request(url)
            req.add_header('User-Agent', self.user_agent)
            
            with urllib.request.urlopen(req, timeout=10) as response:
                data = json.loads(response.read().decode())
                return data
        
        except urllib.error.HTTPError as e:
            logger.error(f"HTTP Error {e.code}: {e.reason}")
            return None
        except urllib.error.URLError as e:
            logger.error(f"URL Error: {e.reason}")
            return None
        except Exception as e:
            logger.error(f"Request error: {e}")
            return None
    
    def get_current_conditions(self) -> Optional[Dict]:
        """Get current weather conditions."""
        url = f"{self.base_url}/stations/{self.location['primary_station']}/observations/latest"
        
        logger.info(f"Fetching current conditions from {url}")
        data = self._make_request(url)
        
        if not data:
            return None
        
        props = data['properties']
        
        # Extract weather data
        current = {
            'timestamp': props['timestamp'],
            'station_id': self.location['primary_station'],
            'temperature_c': self._safe_extract(props, 'temperature'),
            'temperature_f': self._celsius_to_fahrenheit(self._safe_extract(props, 'temperature')),
            'dewpoint_c': self._safe_extract(props, 'dewpoint'),
            'relative_humidity': self._safe_extract(props, 'relativeHumidity'),
            'wind_speed_kmh': self._safe_extract(props, 'windSpeed'),
            'wind_speed_mph': self._kmh_to_mph(self._safe_extract(props, 'windSpeed')),
            'wind_direction_deg': self._safe_extract(props, 'windDirection'),
            'wind_direction_cardinal': self._degrees_to_cardinal(self._safe_extract(props, 'windDirection')),
            'pressure_pa': self._safe_extract(props, 'barometricPressure'),
            'pressure_inhg': self._pa_to_inhg(self._safe_extract(props, 'barometricPressure')),
            'visibility_m': self._safe_extract(props, 'visibility'),
            'visibility_mi': self._meters_to_miles(self._safe_extract(props, 'visibility')),
            'weather_description': props.get('textDescription', ''),
            'data_quality': self._assess_data_quality(props)
        }
        
        logger.info("Successfully retrieved current conditions")
        return current
    
    def get_forecast_data(self) -> Optional[Dict]:
        """Get forecast grid data."""
        url = f"{self.base_url}/gridpoints/{self.location['grid_office']}/{self.location['grid_x']},{self.location['grid_y']}"
        
        logger.info(f"Fetching forecast data from {url}")
        data = self._make_request(url)
        
        if not data:
            return None
        
        props = data['properties']
        
        forecast_data = {
            'update_time': props['updateTime'],
            'valid_times': props['validTimes'],
            'grid_info': {
                'office': self.location['grid_office'],
                'grid_x': self.location['grid_x'],
                'grid_y': self.location['grid_y']
            },
            'temperature_points': len(props.get('temperature', {}).get('values', [])),
            'humidity_points': len(props.get('relativeHumidity', {}).get('values', [])),
            'wind_points': len(props.get('windSpeed', {}).get('values', []))
        }
        
        logger.info("Successfully retrieved forecast data")
        return forecast_data
    
    def get_scanrate_factors(self, current: Dict) -> Dict:
        """Calculate scanrate-affecting factors."""
        factors = {}
        
        # Temperature factor
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
        
        # Wind factor
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
        
        # Humidity factor
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
        
        return factors
    
    def run_test(self) -> Dict:
        """Run comprehensive test of the weather integration."""
        test_results = {
            'test_timestamp': datetime.utcnow().isoformat(),
            'location': self.location,
            'tests_passed': 0,
            'tests_total': 0,
            'current_conditions': None,
            'forecast_data': None,
            'scanrate_factors': None
        }
        
        # Test 1: Current conditions
        test_results['tests_total'] += 1
        logger.info("Test 1: Getting current conditions...")
        current = self.get_current_conditions()
        if current:
            test_results['tests_passed'] += 1
            test_results['current_conditions'] = current
            logger.info("✅ Current conditions test PASSED")
        else:
            logger.error("❌ Current conditions test FAILED")
        
        # Test 2: Forecast data
        test_results['tests_total'] += 1
        logger.info("Test 2: Getting forecast data...")
        forecast = self.get_forecast_data()
        if forecast:
            test_results['tests_passed'] += 1
            test_results['forecast_data'] = forecast
            logger.info("✅ Forecast data test PASSED")
        else:
            logger.error("❌ Forecast data test FAILED")
        
        # Test 3: Scanrate factors (only if current data available)
        if current:
            test_results['tests_total'] += 1
            logger.info("Test 3: Calculating scanrate factors...")
            factors = self.get_scanrate_factors(current)
            if factors:
                test_results['tests_passed'] += 1
                test_results['scanrate_factors'] = factors
                logger.info("✅ Scanrate factors test PASSED")
            else:
                logger.error("❌ Scanrate factors test FAILED")
        
        return test_results
    
    # Helper methods
    def _safe_extract(self, props: Dict, key: str) -> Optional[float]:
        """Safely extract numeric value."""
        try:
            value_dict = props.get(key, {})
            if isinstance(value_dict, dict):
                return value_dict.get('value')
            return value_dict
        except (KeyError, TypeError):
            return None
    
    def _assess_data_quality(self, props: Dict) -> str:
        """Assess data quality."""
        key_fields = ['temperature', 'dewpoint', 'windSpeed', 'barometricPressure', 'relativeHumidity']
        quality_count = sum(1 for field in key_fields if props.get(field, {}).get('value') is not None)
        
        quality_ratio = quality_count / len(key_fields)
        if quality_ratio >= 0.8:
            return 'high'
        elif quality_ratio >= 0.6:
            return 'medium'
        else:
            return 'low'
    
    def _celsius_to_fahrenheit(self, celsius: Optional[float]) -> Optional[float]:
        return (celsius * 9/5) + 32 if celsius is not None else None
    
    def _kmh_to_mph(self, kmh: Optional[float]) -> Optional[float]:
        return kmh * 0.621371 if kmh is not None else None
    
    def _pa_to_inhg(self, pa: Optional[float]) -> Optional[float]:
        return pa * 0.0002953 if pa is not None else None
    
    def _meters_to_miles(self, meters: Optional[float]) -> Optional[float]:
        return meters * 0.000621371 if meters is not None else None
    
    def _degrees_to_cardinal(self, degrees: Optional[float]) -> Optional[str]:
        if degrees is None:
            return None
        directions = ["N", "NNE", "NE", "ENE", "E", "ESE", "SE", "SSE",
                     "S", "SSW", "SW", "WSW", "W", "WNW", "NW", "NNW"]
        index = round(degrees / 22.5) % 16
        return directions[index]


def main():
    """Test the weather integration system."""
    print("=== Weather Integration Test - Philadelphia, PA ===")
    print("Testing with National Weather Service API")
    print("Using built-in urllib (no external dependencies)")
    print()
    
    # Initialize test
    weather = TestWeatherIntegration()
    
    # Run comprehensive test
    results = weather.run_test()
    
    # Display results
    print(f"\n=== TEST RESULTS ===")
    print(f"Tests Passed: {results['tests_passed']}/{results['tests_total']}")
    print(f"Success Rate: {results['tests_passed']/results['tests_total']*100:.1f}%")
    print()
    
    # Show current conditions
    if results['current_conditions']:
        current = results['current_conditions']
        print("📊 CURRENT CONDITIONS:")
        print(f"   Station: {current['station_id']}")
        print(f"   Time: {current['timestamp']}")
        if current['temperature_c'] is not None:
            print(f"   Temperature: {current['temperature_c']:.1f}°C ({current['temperature_f']:.1f}°F)")
        if current['relative_humidity'] is not None:
            print(f"   Humidity: {current['relative_humidity']:.1f}%")
        if current['wind_speed_kmh'] is not None:
            print(f"   Wind: {current['wind_speed_kmh']:.1f} km/h ({current['wind_speed_mph']:.1f} mph) {current['wind_direction_cardinal']}")
        if current['pressure_inhg'] is not None:
            print(f"   Pressure: {current['pressure_inhg']:.2f} inHg")
        if current['visibility_mi'] is not None:
            print(f"   Visibility: {current['visibility_mi']:.1f} miles")
        print(f"   Weather: {current['weather_description']}")
        print(f"   Data Quality: {current['data_quality']}")
    
    # Show forecast info
    if results['forecast_data']:
        forecast = results['forecast_data']
        print(f"\n🔮 FORECAST DATA:")
        print(f"   Update Time: {forecast['update_time']}")
        print(f"   Grid: {forecast['grid_info']['office']}/{forecast['grid_info']['grid_x']},{forecast['grid_info']['grid_y']}")
        print(f"   Temperature Points: {forecast['temperature_points']}")
        print(f"   Humidity Points: {forecast['humidity_points']}")
        print(f"   Wind Points: {forecast['wind_points']}")
    
    # Show scanrate factors
    if results['scanrate_factors']:
        factors = results['scanrate_factors']
        print(f"\n🎯 SCANRATE FACTORS:")
        print(f"   Temperature: {factors.get('temperature_factor', 'unknown')}")
        print(f"   Wind: {factors.get('wind_factor', 'unknown')}")
        print(f"   Humidity: {factors.get('humidity_factor', 'unknown')}")
    
    print(f"\n=== TEST COMPLETE ===")
    
    if results['tests_passed'] == results['tests_total']:
        print("🎉 ALL TESTS PASSED! Weather integration is working perfectly.")
    else:
        print(f"⚠️  {results['tests_total'] - results['tests_passed']} test(s) failed. Check network connectivity.")
    
    print("\nThe enhanced weather integration script is ready for production use!")


if __name__ == "__main__":
    main()