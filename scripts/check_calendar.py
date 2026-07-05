import pandas as pd

def verify_calendar_gaps(file_path="data/salesdaily.csv"):
    """Checks for missing calendar dates in the time-series stream."""
    try:
        df = pd.read_csv(file_path)
        df['datum'] = pd.to_datetime(df['datum'])
        
        # Construct full ideal continuous range
        full_range = pd.date_range(start=df['datum'].min(), end=df['datum'].max(), freq='D')
        
        missing_days = len(full_range) - df['datum'].nunique()
        print(f"Time Series Scope: {df['datum'].min().strftime('%Y-%m-%d')} to {df['datum'].max().strftime('%Y-%m-%d')}")
        print(f"Total Expected Days: {len(full_range)} | Missing Calendar Days: {missing_days}")
    except FileNotFoundError:
        print("Data file not found. Please place salesdaily.csv under data/ directory.")

if __name__ == "__main__":
    verify_calendar_gaps()