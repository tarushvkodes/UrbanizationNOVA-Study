import csv
import os

def clean_aqi_file(input_file):
    cleaned_data = []
    # Add our header - we'll use Date for both daily and yearly data
    cleaned_data.append(['Location', 'Date', 'AQI'])
    
    with open(input_file, 'r') as f:
        # Create a CSV reader that handles quoted fields
        reader = csv.reader(f)
        header = next(reader)
        
        # Determine the file format based on header
        if 'Year' in [h.strip() for h in header]:
            # Yearly format
            for row in reader:
                try:
                    # Handle both space-separated and non-space-separated formats
                    row = [field.strip() for field in row]
                    location = row[0]
                    year = row[1]
                    # Convert the AQI value, handling both integer and float formats
                    aqi = float(row[2])
                    # For yearly data, use the year as the date
                    cleaned_data.append([location, str(year), aqi])
                except (IndexError, ValueError):
                    continue
        else:
            # Daily format
            for row in reader:
                try:
                    if len(row) == 3:  # Simple format
                        location, date, aqi = row
                        aqi = float(aqi)
                        cleaned_data.append([location, date, aqi])
                    elif len(row) >= 11:  # Complex format
                        location = row[2]
                        date = row[4]
                        aqi = float(row[10])
                        cleaned_data.append([location, date, aqi])
                except (IndexError, ValueError):
                    continue
    
    # Generate output filename
    dirname = os.path.dirname(input_file)
    basename = "cleaned_" + os.path.basename(input_file)
    output_file = os.path.join(dirname, basename)
    
    # Write cleaned data
    with open(output_file, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerows(cleaned_data)
    
    print(f"Cleaned data saved to {output_file} with {len(cleaned_data)-1} records")

def main():
    base_dir = os.path.dirname(os.path.realpath(__file__))
    
    # Process each county's AQI file
    for root, _, files in os.walk(base_dir):
        for file in files:
            if ("Air quality index" in file or "AQI" in file) and file.endswith('.csv'):
                if not file.startswith('cleaned_'):  # Skip already cleaned files
                    input_file = os.path.join(root, file)
                    print(f"Processing {file}...")
                    clean_aqi_file(input_file)

if __name__ == "__main__":
    main()