import pandas as pd
import numpy as np
from pathlib import Path
import os

def try_parse_date(date_str):
    """Try different date formats"""
    formats = [
        '%Y-%m-%d',  # 2000-01-01
        '%Y',        # 2000
        '%m/%d/%Y',  # 1/1/2000
        '%Y/%m/%d'   # 2000/01/01
    ]
    
    for fmt in formats:
        try:
            return pd.to_datetime(date_str, format=fmt)
        except:
            continue
    return None

def fill_daily_data(df):
    """Fill in missing days with interpolated values"""
    # Check if this is yearly data (4-digit year) or daily data (full date)
    first_date = str(df['Date'].iloc[0])
    
    # Convert Date to datetime based on format
    if len(first_date) <= 4:  # Yearly format
        # Convert year to start of year date
        df['Date'] = pd.to_datetime(df['Date'].astype(str) + '-01-01')
        # Create daily entries for each year
        dates = []
        locations = []
        values = []
        for _, row in df.iterrows():
            year = row['Date'].year
            # Skip years before 2000
            if year < 2000:
                continue
            daily_dates = pd.date_range(start=f'{year}-01-01', end=f'{year}-12-31', freq='D')
            dates.extend(daily_dates)
            locations.extend([row['Location']] * len(daily_dates))
            values.extend([row['AQI']] * len(daily_dates))
        df = pd.DataFrame({
            'Date': dates,
            'Location': locations,
            'AQI': values
        })
    else:  # Daily format
        # Try parsing each date individually to handle mixed formats
        df['Date'] = df['Date'].apply(try_parse_date)
        
        # Drop any rows where date parsing failed
        df = df.dropna(subset=['Date'])
        
        # Filter for years 2000 and later
        df = df[df['Date'].dt.year >= 2000]
        
        # Handle duplicate dates by taking the mean AQI value for each date
        df = df.groupby(['Date', 'Location'], as_index=False)['AQI'].mean()
    
    # Set Date as index
    df = df.set_index('Date')
    
    # Get the full date range from min to max date
    date_range = pd.date_range(start=df.index.min(), end=df.index.max(), freq='D')
    
    # Reindex to include all dates and forward fill location
    df = df.reindex(date_range)
    df['Location'] = df['Location'].ffill().bfill()
    
    # First interpolate using linear method for accurate transitions
    df['AQI'] = df['AQI'].interpolate(method='linear')
    
    # Fill any remaining NaNs at edges with nearest values
    df['AQI'] = df['AQI'].fillna(method='ffill').fillna(method='bfill')
    
    # Round AQI values to 1 decimal place
    df['AQI'] = df['AQI'].round(1)
    
    # Reset index to make Date a column again
    df = df.reset_index()
    df = df.rename(columns={'index': 'Date'})
    
    return df

def process_files():
    # Get the base directory
    base_dir = Path(__file__).parent
    
    # Process each cleaned AQI file
    for root, _, files in os.walk(base_dir):
        for file in files:
            if file.startswith('cleaned_') and file.endswith('.csv'):
                file_path = os.path.join(root, file)
                print(f"Processing {file}...")
                
                try:
                    # Read the CSV file
                    df = pd.read_csv(file_path)
                    
                    # Fill in missing days
                    df_filled = fill_daily_data(df)
                    
                    # Create output filename
                    output_filename = 'daily_' + file
                    output_path = os.path.join(root, output_filename)
                    
                    # Save the filled data
                    df_filled.to_csv(output_path, index=False)
                    
                    # Print statistics
                    total_days = len(df_filled)
                    missing_values = df_filled['AQI'].isna().sum()
                    date_range = pd.date_range(df_filled['Date'].min(), df_filled['Date'].max())
                    expected_days = len(date_range)
                    
                    print(f"Saved filled daily data to {output_filename}")
                    print(f"Total days: {total_days}")
                    print(f"Expected days: {expected_days}")
                    print(f"Missing values: {missing_values}")
                    print(f"Data completeness: {(total_days-missing_values)/expected_days*100:.1f}%\n")
                    
                except Exception as e:
                    print(f"Error processing {file}: {str(e)}\n")

if __name__ == "__main__":
    process_files()