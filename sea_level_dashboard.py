import streamlit as st
import folium
from streamlit_folium import st_folium
import rasterio
import numpy as np
from PIL import Image
from affected_population_calc import compute_affected_population_and_area_for_given_year_and_sea_level
from process_climate_scenarios import get_scenario

# Load reference GeoTIFF to get bounds
with rasterio.open("cropped.tif") as src:
    bounds = src.bounds
    height = src.height
    width = src.width
    lat_per_pixel = (bounds.top - bounds.bottom) / height
    lon_per_pixel = (bounds.right - bounds.left) / width
    shift_lat_3 = 3 * lat_per_pixel
    shift_lat_2 = 2 * lat_per_pixel
    shift_lon_2 = 2 * lon_per_pixel

pop_image_bounds = [
    [bounds.bottom - shift_lat_3, bounds.left],
    [bounds.top - shift_lat_3, bounds.right]
]
flood_base_bounds = [
    [bounds.bottom - shift_lat_2, bounds.left + shift_lon_2],
    [bounds.top - shift_lat_2, bounds.right + shift_lon_2]
]

# Sidebar controls
st.sidebar.markdown("### Controls")
mode = st.sidebar.radio("Select Mode", ["Scenario", "Custom"])

with st.sidebar.expander("What does each mode mean?"):
    st.markdown("""
    - **Scenario**: Given a climate change scenario, view the affected population and area over the years.
    - **Custom**: Select a specific year and sea level rise (in meters) to view the affected population and area.
    """)
if mode == "Custom":
    year = st.sidebar.slider("Population map for given year", 2024, 2151, 2024, 1)
    sea_level = st.sidebar.slider("Sea Level Rise (m)", 0.0, 10.0, 0.0, 0.1, format="%.1f")
if mode == "Scenario":
    year = st.sidebar.slider("Select a year", 2030, 2150, 2030, 5)
    scenario = st.sidebar.selectbox("Select Scenario", ["SSP1-1.9", "SSP2-4.5", "SSP5-8.5"])

    scenario_df = get_scenario(scenario)
    sea_level = scenario_df.loc[scenario_df['Year'] == year, 'Projected_SLR_m'].values[0]

show_population = st.sidebar.checkbox("Show Population Map", value=True)
show_flood = st.sidebar.checkbox("Show Flood Map", value=True)

st.sidebar.markdown(
    """
    ### About
    This dashboard is an interactive tool to visualize the impact of sea level rise on population density.
    Our project aims to provide insights into the potential consequences of climate change on coastal communities.
    Our project was developed in two parts:
    1. **Estimate sea level rises based on different climate change scenarios**: we used different climate change scenarios (SSP1-1.9, SSP2-4.5, and SSP5-8.5) to estimate potential sea level rises over time.
    2. **What is the estimated population affected by a given rise in sea level**: based on the intersection of inundation maps and population density data.
    """
)

# Process flood image to keep only red pixels
def process_flood_image(path):
    flood_img = Image.open(path).convert("RGB")
    flood_np = np.array(flood_img)
    mask = (
        (flood_np[:, :, 0] > 200) & 
        (flood_np[:, :, 1] < 200) & 
        (flood_np[:, :, 2] < 200)
    )
    binary_map = np.zeros((flood_np.shape[0], flood_np.shape[1], 4), dtype=np.uint8)
    binary_map[mask] = [0, 0, 255, 255]  # Red and opaque
    binary_map[~mask] = [0, 0, 0, 0]     # Fully transparent
    result = Image.fromarray(binary_map)
    result_path = "filtered_flood.png"
    result.save(result_path)
    return result_path

# Create folium map
center_lat = (bounds.top + bounds.bottom) / 2
center_lon = (bounds.left + bounds.right) / 2
m = folium.Map(location=[center_lat, center_lon], zoom_start=7)

# Overlay layers
if show_population:
    population_path = f"Populations/final_population_map{year}.png"
    folium.raster_layers.ImageOverlay(
        name=f"Population Map ({year})",
        image=population_path,
        bounds=pop_image_bounds,
        opacity=0.8,
        interactive=True,
        cross_origin=False
    ).add_to(m)

if show_flood:
    flood_path = f"Resized/{sea_level:.1f}m.png"
    filtered_path = process_flood_image(flood_path)
    folium.raster_layers.ImageOverlay(
        name=f"Flood Map ({sea_level:.1f}m)",
        image=filtered_path,
        bounds=flood_base_bounds,
        opacity=0.8,
        interactive=True,
        cross_origin=False
    ).add_to(m)

folium.LayerControl().add_to(m)

# Display map in Streamlit
st.title("Sea Level Rise Impact Dashboard")
if mode == "Custom":
    st.markdown(
        f"""
    The custom mode allows you to select a specific year and sea level rise (in meters). and calculate the affected population and area.
    The affected area is calculated based on a model by [Climate Central](https://coastal.climatecentral.org/map/8/100.6166/13.2746/?theme=water_level&map_type=water_level_above_mhhw&basemap=roadmap&contiguous=true&elevation_model=best_available&refresh=true&water_level=1.0&water_unit=m).
    The population for a given year is based on a model we developped (see relevant notebook for more details). The data we used is from [Landscan](https://landscan.ornl.gov/), which provides high-resolution population data.
    """)
if mode == "Scenario":
    st.markdown(
        f"""
    The scenario mode allows you to select a climate change scenario and view the affected population and area over the years. The climate change scenarios use combine socioeconomic pathways with greenhouse gas concentration trajectories, representing futures from low (sustainable) to high (fossil-fueled) emissions. Here's a brief overview of the three scenarios used in this project:
    - **SSP1-1.9**: This scenario represents a sustainable world with low greenhouse gas emissions and a focus on global cooperation to achieve climate goals.
    - **SSP2-4.5**: This scenario represents a middle-of-the-road pathway with moderate greenhouse gas emissions and some efforts to mitigate climate change.
    - **SSP5-8.5**: This scenario represents a world with high greenhouse gas emissions and a reliance on fossil fuels, leading to significant climate change impacts.
    
    We then built a Gaussian process model to estimate the sea level rise for each scenario. 
    The affected area is calculated based on a model by [Climate Central](https://coastal.climatecentral.org/map/8/100.6166/13.2746/?theme=water_level&map_type=water_level_above_mhhw&basemap=roadmap&contiguous=true&elevation_model=best_available&refresh=true&water_level=1.0&water_unit=m).
    The population for a given year is based on a model we developped (see relevant notebook for more details). The data we used is from [Landscan](https://landscan.ornl.gov/), which provides high-resolution population data.
    """)
if mode == "Custom":
    st.markdown(f"### Viewing Flood Map for {sea_level:.1f}m Sea Level Rise in {year}")
if mode == "Scenario":
    st.markdown(f"### For scenario {scenario} we predict {sea_level:.1f}m Sea Level Rise by {year}")
st_data = st_folium(m, width=700, height=500)

total_min, total_max, affected_area_km2 = compute_affected_population_and_area_for_given_year_and_sea_level(year, sea_level)
st.markdown(
    f"""
**Predictions for {sea_level:.1f}m Sea Level Rise in {year}:**

- **Affected area:** {affected_area_km2:,.2f} km²  
- **Minimum affected population:** {total_min:,} people  
- **Maximum affected population:** {total_max:,} people
""")
