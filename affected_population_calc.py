from PIL import Image
import numpy as np
import os

color_to_population = {
        (255, 255, 190): (1, 5),
        (255, 255, 115): (6, 25),
        (255, 255, 0): (26, 50),
        (255, 170, 0): (51, 100),
        (255, 102, 0): (101, 500),
        (255, 0, 0): (501, 2500),
        (204, 0, 0): (2501, 5000),
        (115, 0, 0): (5001, 11218), # Replaced 185000 with 11218 (the most densely populated area in the UK)
        (0, 0, 0): (0, 0)
    }

def is_flood_red(pixel):
    r, g, b = pixel
    return (
        r > 200 and
        150 <= g <= 200 and
        150 <= b <= 200
    )
 
def calculate_affected_population_and_area(base_np, flood_np):
    height, width, _ = base_np.shape
    total_min = 0
    total_max = 0
    flood_pixel_count = 0

 
    for y in range(height):
        for x in range(width):
            if is_flood_red(flood_np[y, x]):
                flood_pixel_count += 1
                base_pixel = tuple(base_np[y, x].tolist())
                if base_pixel in color_to_population:
                    pop_min, pop_max = color_to_population[base_pixel]
                    total_min += pop_min
                    total_max += pop_max
 
    pixel_length_km = 20 / 51
    pixel_area_km2 = pixel_length_km ** 2
    affected_area_km2 = flood_pixel_count * pixel_area_km2
 
    return total_min, total_max, affected_area_km2

def compute_affected_population_and_area_for_given_year_and_sea_level(year, sea_level):
    base_map_path = f"Populations/final_population_map{year}.png"
    flood_folder = "Resized/"
    
    
    base_img = Image.open(base_map_path).convert("RGB")
    base_np = np.array(base_img)

    filename = f"{sea_level:.1f}m.png"
    flood_path = os.path.join(flood_folder, filename)
    init_flood_path = os.path.join(flood_folder, "0.0m.png")

    flood_img = Image.open(flood_path).convert("RGB")
    flood_np = np.array(flood_img)
    init_flood_img = Image.open(init_flood_path).convert("RGB")
    init_flood_np = np.array(init_flood_img)

    # calculate_affected_population_and_area returns a tuple (pop_min, pop_max, area)
    result1 = calculate_affected_population_and_area(base_np, flood_np)
    result0 = calculate_affected_population_and_area(base_np, init_flood_np)
    return tuple(a - b for a, b in zip(result1, result0))