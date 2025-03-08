import pandas as pd
import numpy as np
from pathlib import Path
import os

def load_and_prepare_aqi_data(file_path):
    # Read the CSV file
    df = pd.read_csv(file_path)
    
    # Check if this is yearly or daily data by looking at the first date
    first_date = df['Date'].iloc[0]
    
    if len(str(first_date)) <= 4:  # Yearly format (YYYY)
        # Convert year to daily dates
        df['Date'] = pd.to_datetime(df['Date'].astype(str) + '-01-01')
        df = df.set_index('Date')
        
        # Create daily entries for each year
        new_data = []
        for year in df.index.year.unique():
            year_data = df[df.index.year == year]
            dates = pd.date_range(start=f'{year}-01-01', end=f'{year}-12-31', freq='D')
            for date in dates:
                new_data.append({
                    'Date': date,
                    'Location': year_data['Location'].iloc[0],
                    'AQI': year_data['AQI'].iloc[0]
                })
        df = pd.DataFrame(new_data)
        df.set_index('Date', inplace=True)
    else:
        # Handle daily format
        df['Date'] = pd.to_datetime(df['Date'])
        df.set_index('Date', inplace=True)
    
    # Sort by date
    df.sort_index(inplace=True)
    
    return df

def interpolate_county_data(df):
    # For daily data, interpolate gaps
    df_daily = df.copy()
    
    # Use linear interpolation for gaps up to 7 days
    df_daily['AQI'] = df_daily['AQI'].interpolate(method='linear', limit=7)
    
    return df_daily

def main():
    # Get the base directory
    base_dir = Path(__file__).parent
    
    # Dictionary to store data frames for each county
    county_data = {}
    
    # Find all cleaned AQI files
    for root, _, files in os.walk(base_dir):
        for file in files:
            if file.startswith('cleaned_') and ('Air quality index' in file or 'AQI' in file):
                file_path = os.path.join(root, file)
                print(f"Processing {file}...")
                
                try:
                    # Load and prepare the data
                    df = load_and_prepare_aqi_data(file_path)
                    county_name = df['Location'].iloc[0]
                    
                    # Store the dataframe
                    county_data[county_name] = df
                    print(f"Successfully loaded {county_name} data with {len(df)} records")
                except Exception as e:
                    print(f"Skipping {file} due to error: {str(e)}")
                    continue
    
    if not county_data:
        print("No valid data files were processed")
        return
    
    # Find the common date range
    start_dates = []
    end_dates = []
    for df in county_data.values():
        start_dates.append(df.index.min())
        end_dates.append(df.index.max())
    
    common_start = max(start_dates)
    common_end = min(end_dates)
    
    print(f"\nCommon date range: {common_start.date()} to {common_end.date()}")
    
    # Interpolate data for each county within the common date range
    interpolated_data = {}
    for county, df in county_data.items():
        # Filter to common date range
        df_filtered = df[common_start:common_end]
        
        # Interpolate
        df_interpolated = interpolate_county_data(df_filtered)
        
        # Store interpolated data
        interpolated_data[county] = df_interpolated
    
    # Create a combined dataframe with all counties
    combined_df = pd.DataFrame()
    for county, df in interpolated_data.items():
        combined_df[county] = df['AQI']
    
    # Save interpolated data
    output_path = base_dir / 'interpolated_aqi_data.csv'
    combined_df.to_csv(output_path)
    print(f"\nInterpolated data saved to {output_path}")
    
    # Print statistics
    print("\nInterpolation statistics:")
    for county in combined_df.columns:
        missing = combined_df[county].isna().sum()
        total = len(combined_df)
        print(f"{county}:")
        print(f"  Total days: {total}")
        print(f"  Missing values after interpolation: {missing} ({missing/total*100:.1f}%)")

if __name__ == "__main__":
    main()