import os
import shutil
import argparse
from PIL import Image

output_dir = os.path.join('./temp-1')

def split_image(image_path, tile_width, tile_height):
    img = Image.open(image_path)
    img_width, img_height = img.size
    print(f"Image size: {img_width} x {img_height}")

    for i in range(0, img_width, tile_width):
        for j in range(0, img_height, tile_height):
            box = (i, j, min(i + tile_width, img_width), min(j + tile_height, img_height))
            img_crop = img.crop(box)
            
            img_crop.save(os.path.join(output_dir, f"tile_{tile_width}_{i}_{tile_height}_{j}.png"))

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--height_map", type=str)
    args = parser.parse_args()
    
    shutil.rmtree(output_dir, ignore_errors=True)
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    tile_width = 600
    tile_height = 600

    split_image(args.height_map, tile_width, tile_height)
