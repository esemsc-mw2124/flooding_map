
import streamlit as st
import folium
from streamlit_folium import st_folium
import rasterio
import numpy as np
from PIL import Image

# File paths
population_image_path = "final_population_map.png"

# Load reference GeoTIFF to get bounds
with rasterio.open("cropped.tif") as src:
    bounds = src.bounds
    height = src.height
    width = src.width
    lat_per_pixel = (bounds.top - bounds.bottom) / height
    lon_per_pixel = (bounds.right - bounds.left) / width
    shift_lat_5 = 5 * lat_per_pixel
    shift_lat_2 = 2 * lat_per_pixel
    shift_lon_2 = 2 * lon_per_pixel

pop_image_bounds = [
    [bounds.bottom - shift_lat_5, bounds.left],
    [bounds.top - shift_lat_5, bounds.right]
]
flood_base_bounds = [
    [bounds.bottom - shift_lat_2, bounds.left + shift_lon_2],
    [bounds.top - shift_lat_2, bounds.right + shift_lon_2]
]

# Sidebar controls
st.sidebar.title("Controls")
sea_level = st.sidebar.slider("Sea Level Rise (m)", 0.0, 10.0, 0.0, 0.1, format="%.1f")
show_population = st.sidebar.checkbox("Show Population Map", value=True)
show_flood = st.sidebar.checkbox("Show Flood Map", value=True)

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
    folium.raster_layers.ImageOverlay(
        name="Population Map",
        image=population_image_path,
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
st.title("Sea Level Rise Impact Viewer")
st.markdown(f"### Viewing Flood Map for {sea_level:.1f}m Sea Level Rise")
st_data = st_folium(m, width=700, height=500)
