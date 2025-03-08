import pandas as pd
import os
from pathlib import Path

def aggregate_to_yearly(file_path):
    """Convert daily AQI data to yearly averages"""
    # Read the daily data
    df = pd.read_csv(file_path)
    
    # Convert Date to datetime
    df['Date'] = pd.to_datetime(df['Date'])
    
    # Filter for years 2000 and later
    df = df[df['Date'].dt.year >= 2000]
    
    # Extract year from date
    df['Year'] = df['Date'].dt.year
    
    # Group by Location and Year to get averages
    yearly_df = df.groupby(['Location', 'Year'])['AQI'].mean().reset_index()
    
    # Round AQI to 1 decimal place
    yearly_df['AQI'] = yearly_df['AQI'].round(1)
    
    # Convert Year back to string format for consistency
    yearly_df['Year'] = yearly_df['Year'].astype(str)
    
    # Rename Year column to Date for consistency with format
    yearly_df = yearly_df.rename(columns={'Year': 'Date'})
    
    # Create output filename
    dirname = os.path.dirname(file_path)
    basename = os.path.basename(file_path)
    yearly_basename = 'yearly_' + basename
    output_path = os.path.join(dirname, yearly_basename)
    
    # Save to CSV
    yearly_df.to_csv(output_path, index=False)
    print(f"Saved yearly averages to {output_path}")
    return yearly_df

def process_all_counties():
    # Get the base directory
    base_dir = Path(__file__).parent
    
    # Process each daily cleaned file
    yearly_data = []
    for root, _, files in os.walk(base_dir):
        for file in files:
            if file.startswith('daily_cleaned_') and file.endswith('.csv'):
                file_path = os.path.join(root, file)
                print(f"Processing {file}...")
                yearly_df = aggregate_to_yearly(file_path)
                yearly_data.append(yearly_df)
    
    # Combine all yearly data into one file
    if yearly_data:
        combined_df = pd.concat(yearly_data, ignore_index=True)
        combined_df = combined_df.sort_values(['Location', 'Date'])
        
        # Save combined yearly data
        output_path = base_dir / 'combined_yearly_aqi.csv'
        combined_df.to_csv(output_path, index=False)
        print(f"\nSaved combined yearly data to {output_path}")
        
        # Print summary statistics
        print("\nSummary of yearly data:")
        for location in combined_df['Location'].unique():
            loc_data = combined_df[combined_df['Location'] == location]
            print(f"\n{location}:")
            print(f"  Years covered: {loc_data['Date'].min()} - {loc_data['Date'].max()}")
            print(f"  Average AQI: {loc_data['AQI'].mean():.1f}")
            print(f"  Number of years: {len(loc_data)}")

if __name__ == "__main__":
    process_all_counties()