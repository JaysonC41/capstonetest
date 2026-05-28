from __future__ import annotations

import argparse
from pathlib import Path
from typing import Optional

import pandas as pd
import requests

NYC_LATITUDE = 40.7128
NYC_LONGITUDE = -74.0060
OPEN_METEO_ARCHIVE_URL = "https://archive-api.open-meteo.com/v1/archive"

DEFAULT_INPUT_PATH = Path("data/parking_violations_final.csv")
DEFAULT_OUTPUT_PATH = Path("data/parking_violations_with_weather.csv")
DEFAULT_WEATHER_CACHE_PATH = Path("data/nyc_weather_daily.csv")


WEATHER_CODE_MAP = {
    0: "Clear sky",
    1: "Mainly clear",
    2: "Partly cloudy",
    3: "Overcast",
    45: "Fog",
    48: "Depositing rime fog",
    51: "Light drizzle",
    53: "Moderate drizzle",
    55: "Dense drizzle",
    56: "Light freezing drizzle",
    57: "Dense freezing drizzle",
    61: "Slight rain",
    63: "Moderate rain",
    65: "Heavy rain",
    66: "Light freezing rain",
    67: "Heavy freezing rain",
    71: "Slight snow fall",
    73: "Moderate snow fall",
    75: "Heavy snow fall",
    77: "Snow grains",
    80: "Slight rain showers",
    81: "Moderate rain showers",
    82: "Violent rain showers",
    85: "Slight snow showers",
    86: "Heavy snow showers",
    95: "Thunderstorm",
    96: "Thunderstorm with slight hail",
    99: "Thunderstorm with heavy hail",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Enrich NYC parking tickets with historical daily weather from Open-Meteo."
    )
    parser.add_argument(
        "--input",
        type=Path,
        default=DEFAULT_INPUT_PATH,
        help=f"Parking violations CSV to enrich (default: {DEFAULT_INPUT_PATH})",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT_PATH,
        help=f"Output CSV path (default: {DEFAULT_OUTPUT_PATH})",
    )
    parser.add_argument(
        "--weather-cache",
        type=Path,
        default=DEFAULT_WEATHER_CACHE_PATH,
        help=f"Weather cache CSV path (default: {DEFAULT_WEATHER_CACHE_PATH})",
    )
    parser.add_argument(
        "--force-refresh",
        action="store_true",
        help="Ignore cached weather data and refetch from the API.",
    )
    return parser.parse_args()


# def load_parking_data(input_path: Path) -> pd.DataFrame:
#     if not input_path.exists():
#         raise FileNotFoundError(f"Input file not found: {input_path}")

#     df = pd.read_csv(input_path)

#     if "issue_date" not in df.columns:
#         raise ValueError("Input data must contain an 'issue_date' column.")

#     df["issue_date"] = pd.to_datetime(df["issue_date"], errors="coerce")
#     df["issue_date_only"] = df["issue_date"].dt.normalize()

#     return df


def fetch_weather_daily(
    start_date: pd.Timestamp,
    end_date: pd.Timestamp,
    *,
    cache_path: Path,
    force_refresh: bool = False,
) -> pd.DataFrame:
    if cache_path.exists() and not force_refresh:
        cached = pd.read_csv(cache_path)
        if "weather_date" in cached.columns:
            cached["weather_date"] = pd.to_datetime(cached["weather_date"], errors="coerce").dt.normalize()
            cached = cached.dropna(subset=["weather_date"])

            cached_min = cached["weather_date"].min()
            cached_max = cached["weather_date"].max()

            if pd.notna(cached_min) and pd.notna(cached_max) and cached_min <= start_date and cached_max >= end_date:
                return cached[(cached["weather_date"] >= start_date) & (cached["weather_date"] <= end_date)].copy()

    weather_frames: list[pd.DataFrame] = []

    def fetch_chunk(chunk_start: pd.Timestamp, chunk_end: pd.Timestamp) -> pd.DataFrame:
        params = {
            "latitude": NYC_LATITUDE,
            "longitude": NYC_LONGITUDE,
            "start_date": chunk_start.strftime("%Y-%m-%d"),
            "end_date": chunk_end.strftime("%Y-%m-%d"),
            "daily": ",".join(
                [
                    "weather_code",
                    "temperature_2m_max",
                    "temperature_2m_min",
                    "precipitation_sum",
                    "wind_speed_10m_max",
                ]
            ),
            "timezone": "America/New_York",
        }

        response = requests.get(OPEN_METEO_ARCHIVE_URL, params=params, timeout=120)
        response.raise_for_status()

        payload = response.json()
        daily = payload.get("daily")

        if not daily or "time" not in daily:
            raise ValueError(
                f"Open-Meteo response did not include daily weather data for {chunk_start.date()} to {chunk_end.date()}."
            )

        chunk = pd.DataFrame(daily)
        chunk = chunk.rename(columns={"time": "weather_date"})
        chunk["weather_date"] = pd.to_datetime(chunk["weather_date"], errors="coerce").dt.normalize()
        chunk["weather_condition"] = chunk["weather_code"].map(WEATHER_CODE_MAP).fillna("Unknown")
        return chunk

    current_start = start_date.normalize()
    final_end = end_date.normalize()

    while current_start <= final_end:
        chunk_end = min(current_start + pd.offsets.YearEnd(0), final_end)
        weather_frames.append(fetch_chunk(current_start, chunk_end))
        current_start = chunk_end + pd.Timedelta(days=1)

    weather = pd.concat(weather_frames, ignore_index=True)
    weather = weather.dropna(subset=["weather_date"])
    weather = weather.drop_duplicates(subset=["weather_date"]).sort_values("weather_date").reset_index(drop=True)

    cache_path.parent.mkdir(parents=True, exist_ok=True)
    weather.to_csv(cache_path, index=False)

    return weather


def enrich_with_weather(
    parking_df: pd.DataFrame,
    weather_df: pd.DataFrame,
) -> pd.DataFrame:
    enriched = parking_df.merge(
        weather_df,
        left_on="issue_date_only",
        right_on="weather_date",
        how="left",
    )

    enriched["weather_available"] = enriched["weather_code"].notna()

    return enriched


def main() -> None:
    print("Starting weather enrichment...")
    args = parse_args()

    if not args.input.exists():
        raise FileNotFoundError(f"Input file not found: {args.input}")

    print("Scanning issue dates...")

    date_chunks = []

    for chunk in pd.read_csv(
        args.input,
        usecols=["issue_date"],
        chunksize=100000,
    ):
        chunk["issue_date"] = pd.to_datetime(
            chunk["issue_date"],
            errors="coerce"
        )

        valid_dates = chunk["issue_date"].dropna()

        if not valid_dates.empty:
            date_chunks.append(valid_dates)

    all_dates = pd.concat(date_chunks)

    start_date = all_dates.min()
    end_date = all_dates.max()

    print(f"Loading weather for {start_date.date()} to {end_date.date()}")

    weather = fetch_weather_daily(
        start_date,
        end_date,
        cache_path=args.weather_cache,
        force_refresh=args.force_refresh,
    )

    print(f"Loaded {len(weather):,} weather rows")

    args.output.parent.mkdir(parents=True, exist_ok=True)

    first_chunk = True

    print("Beginning chunk processing...")

    for i, chunk in enumerate(
        pd.read_csv(args.input, chunksize=100000)
    ):

        print(f"Loaded chunk {i + 1}")

        chunk["issue_date"] = pd.to_datetime(
            chunk["issue_date"],
            errors="coerce"
        )

        chunk["issue_date_only"] = (
            chunk["issue_date"]
            .dt.normalize()
        )

        enriched = enrich_with_weather(chunk, weather)

        print(f"Finished enriching chunk {i + 1}")

        enriched.to_csv(
            args.output,
            mode="w" if first_chunk else "a",
            header=first_chunk,
            index=False,
        )

        print(f"Saved chunk {i + 1}")

        first_chunk = False
        print(f"Saved enriched dataset to {args.output}")


if __name__ == "__main__":
    main()
