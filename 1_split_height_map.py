import os
import shutil
import configparser
from PIL import Image, ImageOps
Image.MAX_IMAGE_PIXELS = None

output_dir = os.path.join('./temp-1')

def split_image(image_path, tile_size: int):
    image = Image.open(image_path)
    image_width, image_height = image.size
    print(f"Image size: {image_width} x {image_height}")
    
    pad_width = (tile_size - image_width % tile_size) % tile_size
    pad_height = (tile_size - image_height % tile_size) % tile_size
    
    if image.mode == 'RGB':
        fill_color = (0, 0, 0)
    elif image.mode in ['L', 'I;16']:
        fill_color = 0
    else:
        raise ValueError(f"지원되지 않는 이미지 모드: {image.mode}")
    
    padded_image = ImageOps.expand(image, (0, 0, pad_width, pad_height), fill=fill_color)
    padded_image.save(os.path.join(output_dir, "padded_image.png"))
    
    padded_width, padded_height = padded_image.size
    print(f"Padded image size: {padded_width} x {padded_height}")

    # 패딩된 이미지에서 타일 분할
    for z in range(0, padded_height, tile_size):
        for x in range(0, padded_width, tile_size):
            tile = padded_image.crop((x, z, x + tile_size, z + tile_size))
            tile.save(os.path.join(output_dir, f"tile_{tile_size}_{x}_{z}.png"))

if __name__ == "__main__":
    config = configparser.ConfigParser()
    config.read('config.ini')
    
    height_map = config['DEFAULT']['height_map']
    tile_size = int(config['DEFAULT']['tile_size'])
    scale = int(config['DEFAULT']['scale'])

    assert int(tile_size * (scale / 100)) % 512 == 0, "Tile size * scale must be divisible by 512."
    
    shutil.rmtree(output_dir, ignore_errors=True)
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    split_image(height_map, tile_size)
