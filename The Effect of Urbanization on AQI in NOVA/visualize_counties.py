import folium
import json
import pandas as pd
from shapely.geometry import Polygon, mapping
import geopandas as gpd
from shapely.geometry import shape

def create_county_map():
    # Define counties with their more accurate boundary coordinates
    counties = {
        'Fairfax': {
            'state': 'VA',
            'coords': [
                [-77.31, 38.71], [-77.31, 38.98], [-77.12, 38.98],
                [-77.12, 38.84], [-77.04, 38.84], [-77.04, 38.71],
                [-77.31, 38.71]
            ]
        },
        'Frederick': {
            'state': 'MD',
            'coords': [
                [-77.69, 39.21], [-77.69, 39.72], [-77.16, 39.72],
                [-77.16, 39.21], [-77.69, 39.21]
            ]
        },
        'Howard': {
            'state': 'MD',
            'coords': [
                [-77.01, 39.13], [-77.01, 39.34], [-76.71, 39.34],
                [-76.71, 39.13], [-77.01, 39.13]
            ]
        },
        'Montgomery': {
            'state': 'MD',
            'coords': [
                [-77.33, 38.93], [-77.33, 39.28], [-76.97, 39.28],
                [-76.97, 38.93], [-77.33, 38.93]
            ]
        },
        'Prince Georges': {
            'state': 'MD',
            'coords': [
                [-76.97, 38.7], [-76.97, 39.1], [-76.71, 39.1],
                [-76.71, 38.7], [-76.97, 38.7]
            ]
        },
        'Loudoun': {
            'state': 'VA',
            'coords': [
                [-77.95, 38.83], [-77.95, 39.33], [-77.31, 39.33],
                [-77.31, 38.83], [-77.95, 38.83]
            ]
        },
        'Prince William': {
            'state': 'VA',
            'coords': [
                [-77.65, 38.53], [-77.65, 38.88], [-77.31, 38.88],
                [-77.31, 38.53], [-77.65, 38.53]
            ]
        },
        'Arlington': {
            'state': 'VA',
            'coords': [
                [-77.17, 38.83], [-77.17, 38.93], [-77.04, 38.93],
                [-77.04, 38.83], [-77.17, 38.83]
            ]
        },
        'Alexandria': {
            'state': 'VA',
            'coords': [
                [-77.14, 38.77], [-77.14, 38.86], [-77.04, 38.86],
                [-77.04, 38.77], [-77.14, 38.77]
            ]
        },
        'District of Columbia': {
            'state': 'DC',
            'coords': [
                [-77.12, 38.79], [-77.12, 38.995], [-76.909, 38.995],
                [-76.909, 38.79], [-77.12, 38.79]
            ]
        }
    }

    # Create GeoJSON features
    features = []
    for name, data in counties.items():
        polygon = Polygon(data['coords'])
        feature = {
            'type': 'Feature',
            'properties': {
                'name': name,
                'state': data['state']
            },
            'geometry': mapping(polygon)
        }
        features.append(feature)

    # Create GeoJSON object
    geojson_data = {
        'type': 'FeatureCollection',
        'features': features
    }

    # Create map centered on DC area with a lighter background
    m = folium.Map(
        location=[38.9072, -77.0369],
        zoom_start=9,
        tiles='cartodbpositron'
    )

    # Colors for different states with better contrast
    state_colors = {
        'VA': '#FF8080',  # Lighter red
        'MD': '#8080FF',  # Lighter blue
        'DC': '#80FF80'   # Lighter green
    }

    # Add county boundaries to map with improved styling
    folium.GeoJson(
        geojson_data,
        name='Counties',
        style_function=lambda feature: {
            'fillColor': state_colors[feature['properties']['state']],
            'color': 'black',
            'weight': 1.5,
            'fillOpacity': 0.4,
            'dashArray': '3'
        },
        highlight_function=lambda x: {
            'weight': 3,
            'fillOpacity': 0.7
        },
        tooltip=folium.GeoJsonTooltip(
            fields=['name', 'state'],
            aliases=['County', 'State'],
            style=("background-color: white; color: #333333; font-family: arial; font-size: 12px; padding: 10px;")
        )
    ).add_to(m)

    # Add county labels
    for feature in geojson_data['features']:
        coords = feature['geometry']['coordinates'][0]
        center_lat = sum(coord[1] for coord in coords) / len(coords)
        center_lon = sum(coord[0] for coord in coords) / len(coords)
        
        folium.Popup(
            f"{feature['properties']['name']}, {feature['properties']['state']}",
            parse_html=True
        ).add_to(folium.Marker(
            [center_lat, center_lon],
            icon=folium.DivIcon(
                html=f'<div style="font-size: 10pt; color: black; text-shadow: -1px -1px 0 white, 1px -1px 0 white, -1px 1px 0 white, 1px 1px 0 white; font-weight: bold; background: none; border: none">{feature["properties"]["name"]}</div>'
            )
        )).add_to(m)

    # Add legend with improved styling
    legend_html = """
    <div style="position: fixed; 
                bottom: 50px; right: 50px; width: 180px; height: 130px; 
                border:1px solid grey; z-index:9999; background-color:white;
                opacity:0.9; padding:10px; border-radius: 5px; box-shadow: 0 0 5px rgba(0,0,0,0.2)">
        <p style="margin-top: 0; font-weight: bold;">Counties by State</p>
        <p><span style="background-color: #FF8080; opacity: 0.6; padding: 0 10px; border: 1px solid black">&nbsp;</span> Virginia</p>
        <p><span style="background-color: #8080FF; opacity: 0.6; padding: 0 10px; border: 1px solid black">&nbsp;</span> Maryland</p>
        <p><span style="background-color: #80FF80; opacity: 0.6; padding: 0 10px; border: 1px solid black">&nbsp;</span> DC</p>
    </div>
    """
    m.get_root().html.add_child(folium.Element(legend_html))

    # Save the map
    output_path = 'county_map.html'
    m.save(output_path)
    print(f"\nMap has been saved as '{output_path}'")
    print("Open this file in a web browser to view the interactive map of the studied counties.")

if __name__ == "__main__":
    create_county_map()