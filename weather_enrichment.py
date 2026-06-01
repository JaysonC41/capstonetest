"""
weather_enrichment.py
Adds weather data to NYC parking violations CSV without loading entire file.
"""

import pandas as pd
import requests
import os
import sys
from datetime import datetime, timedelta
import argparse
import logging

# Set up logging - FIXED QUOTES
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# NYC Central Park coordinates
LATITUDE = 40.7831
LONGITUDE = -73.9712

def get_date_range_fast(input_file, date_column='issue_date'):
    """
    Get min and max dates WITHOUT loading entire file.
    Uses pandas with low_memory and only reads the date column.
    """
    logger.info(f"Scanning {input_file} for date range...")
    
    try:
        # Read only the date column in chunks
        min_date = None
        max_date = None
        chunk_count = 0
        
        for chunk in pd.read_csv(input_file, 
                                  usecols=[date_column], 
                                  chunksize=100000,
                                  low_memory=False):
            # Convert to datetime, coercing errors
            chunk_dates = pd.to_datetime(chunk[date_column], errors='coerce')
            
            # Drop NaT values
            chunk_dates = chunk_dates.dropna()
            
            if len(chunk_dates) > 0:
                chunk_min = chunk_dates.min()
                chunk_max = chunk_dates.max()
                
                if min_date is None or chunk_min < min_date:
                    min_date = chunk_min
                if max_date is None or chunk_max > max_date:
                    max_date = chunk_max
            
            chunk_count += 1
            if chunk_count % 10 == 0:
                logger.info(f"  Processed {chunk_count * 100000:,} rows...")
        
        logger.info(f"✅ Date range found: {min_date.date()} to {max_date.date()}")
        return min_date, max_date
        
    except Exception as e:
        logger.error(f"Error reading date column: {e}")
        # Fallback: return default range
        logger.info("Using default date range (2020-2025)")
        return datetime(2020, 1, 1), datetime(2025, 12, 31)

def fetch_weather_data(start_date, end_date):
    """
    Fetch weather data from Open-Meteo API.
    """
    logger.info(f"Fetching weather data from {start_date.date()} to {end_date.date()}...")
    
    # Format dates for API
    start_str = start_date.strftime('%Y-%m-%d')
    end_str = end_date.strftime('%Y-%m-%d')
    
    url = "https://archive-api.open-meteo.com/v1/archive"
    params = {
        "latitude": LATITUDE,
        "longitude": LONGITUDE,
        "start_date": start_str,
        "end_date": end_str,
        "daily": [
            "temperature_2m_max",
            "temperature_2m_min", 
            "temperature_2m_mean",
            "precipitation_sum",
            "rain_sum",
            "snowfall_sum",
            "precipitation_hours",
            "wind_speed_10m_max"
        ],
        "temperature_unit": "fahrenheit",
        "timezone": "America/New_York"
    }
    
    try:
        response = requests.get(url, params=params, timeout=60)
        response.raise_for_status()
        data = response.json()
        
        # Convert to DataFrame
        weather_df = pd.DataFrame(data['daily'])
        weather_df['date'] = pd.to_datetime(weather_df['time'])
        
        # Rename columns for clarity
        weather_df.rename(columns={
            'temperature_2m_max': 'temp_max_f',
            'temperature_2m_min': 'temp_min_f',
            'temperature_2m_mean': 'temp_mean_f',
            'precipitation_sum': 'precipitation_inches',
            'rain_sum': 'rain_inches',
            'snowfall_sum': 'snow_inches',
            'precipitation_hours': 'precip_hours',
            'wind_speed_10m_max': 'wind_max_mph'
        }, inplace=True)
        
        # Add derived columns
        weather_df['rain_day'] = (weather_df['rain_inches'] > 0).astype(int)
        weather_df['snow_day'] = (weather_df['snow_inches'] > 0).astype(int)
        weather_df['extreme_temp_day'] = ((weather_df['temp_max_f'] > 90) | 
                                          (weather_df['temp_min_f'] < 32)).astype(int)
        
        logger.info(f"✅ Fetched {len(weather_df)} days of weather data")
        return weather_df
        
    except Exception as e:
        logger.error(f"API request failed: {e}")
        return None

def enrich_with_weather(input_file, output_file, weather_df):
    """
    Add weather data to parking violations CSV.
    Processes in chunks to handle large files.
    """
    logger.info(f"Enriching {input_file} with weather data...")
    
    # Create date lookup dictionary for quick access
    weather_dict = weather_df.set_index('date').to_dict('index')
    
    # Process in chunks
    chunk_size = 100000
    first_chunk = True
    total_rows = 0
    matched_rows = 0
    
    for chunk in pd.read_csv(input_file, chunksize=chunk_size, low_memory=False):
        original_len = len(chunk)
        
        # Convert issue_date to datetime
        chunk['issue_date'] = pd.to_datetime(chunk['issue_date'], errors='coerce')
        
        # Extract date part only (for matching)
        chunk['date'] = chunk['issue_date'].dt.date
        
        # Add weather columns
        chunk['temp_max_f'] = chunk['date'].apply(lambda d: weather_dict.get(d, {}).get('temp_max_f', pd.NA))
        chunk['temp_min_f'] = chunk['date'].apply(lambda d: weather_dict.get(d, {}).get('temp_min_f', pd.NA))
        chunk['temp_mean_f'] = chunk['date'].apply(lambda d: weather_dict.get(d, {}).get('temp_mean_f', pd.NA))
        chunk['precipitation_inches'] = chunk['date'].apply(lambda d: weather_dict.get(d, {}).get('precipitation_inches', pd.NA))
        chunk['rain_day'] = chunk['date'].apply(lambda d: weather_dict.get(d, {}).get('rain_day', pd.NA))
        chunk['snow_day'] = chunk['date'].apply(lambda d: weather_dict.get(d, {}).get('snow_day', pd.NA))
        
        # Count matches
        matched_rows += chunk['temp_max_f'].notna().sum()
        total_rows += original_len
        
        # Drop the temporary date column
        chunk = chunk.drop(columns=['date'])
        
        # Write chunk
        chunk.to_csv(output_file, 
                     mode='w' if first_chunk else 'a',
                     header=first_chunk,
                     index=False)
        first_chunk = False
        
        logger.info(f"  Processed {total_rows:,} rows ({matched_rows:,} matched to weather)")
    
    logger.info(f"✅ Enrichment complete!")
    logger.info(f"   Total rows: {total_rows:,}")
    logger.info(f"   Matched to weather: {matched_rows:,} ({matched_rows/total_rows*100:.1f}%)")
    
    return total_rows, matched_rows

def main():
    parser = argparse.ArgumentParser(description='Add weather data to parking violations CSV')
    parser.add_argument('input', help='Input CSV file path')
    parser.add_argument('output', help='Output CSV file path')
    parser.add_argument('--start-date', help='Start date (YYYY-MM-DD)', default=None)
    parser.add_argument('--end-date', help='End date (YYYY-MM-DD)', default=None)
    parser.add_argument('--no-date-scan', action='store_true', help='Skip scanning for date range')
    
    args = parser.parse_args()
    
    logger.info("Starting weather enrichment...")
    
    # Check input file exists
    if not os.path.exists(args.input):
        logger.error(f"Input file not found: {args.input}")
        sys.exit(1)
    
    # Get date range
    if args.start_date and args.end_date and args.no_date_scan:
        start_date = datetime.strptime(args.start_date, '%Y-%m-%d')
        end_date = datetime.strptime(args.end_date, '%Y-%m-%d')
        logger.info(f"Using provided date range: {start_date.date()} to {end_date.date()}")
    else:
        # Fast scan of date column
        start_date, end_date = get_date_range_fast(args.input)
    
    # Fetch weather data
    weather_df = fetch_weather_data(start_date, end_date)
    
    if weather_df is None or len(weather_df) == 0:
        logger.error("Failed to fetch weather data")
        sys.exit(1)
    
    # Enrich the data
    total, matched = enrich_with_weather(args.input, args.output, weather_df)
    
    logger.info(f"\n🎉 Done! Weather-enriched file saved to: {args.output}")

if __name__ == "__main__":
    main()