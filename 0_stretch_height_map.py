import os
import configparser
from PIL import Image
import numpy as np
Image.MAX_IMAGE_PIXELS = None


MAX_HEIGHT_8 = 255.0
MIN_HEIGHT_8 = 0.0 # 8.0 * 8 # for water level
MAX_HEIGHT_16 = 65535.0
MIN_HEIGHT_16 = 0.0 # 1024.0 * 9

def max_height(image_path):
    """
    주어진 height map 이미지의 최대 높이를 반환합니다.
    지원되는 비트 깊이: 8비트 ('L'), 16비트 ('I;16')
    
    Parameters:
        image_path (str): height map 이미지 파일의 경로.
        
    Returns:
        int: 이미지의 최대 높이 값.
    """
    # 이미지 불러오기
    height_map_image = Image.open(image_path)
    
    if height_map_image.mode == 'RGBA':
        # 이미지를 그레이스케일로 변환
        height_map_image = height_map_image.convert('L')
        print("RGBA 이미지를 그레이스케일로 변환했습니다.")
    
    # 이미지 모드에 따라 처리
    if height_map_image.mode == 'L':
        # 8비트 그레이스케일 이미지
        pixels = np.array(height_map_image)
        max_height = np.max(pixels)
        print("이미지는 8비트 그레이스케일 형식입니다.")
    elif height_map_image.mode == 'I;16':
        # 16비트 그레이스케일 이미지
        pixels = np.array(height_map_image)
        max_height = np.max(pixels)
        print("이미지는 16비트 그레이스케일 형식입니다.")
    else:
        raise ValueError(f"지원되지 않는 이미지 형식입니다: {height_map_image.mode}. 8비트('L') 또는 16비트('I;16') 그레이스케일 이미지를 사용해주세요.")
    
    return max_height

def apply_scaling(height_map):
    max_height = np.max(height_map)
    
    
    T1 = 1
    T2 = 2
    T3 = 5
    T4 = 10
    T5 = max_height / 3
    T6 = 2 * max_height / 3
    
    W1 = 2
    W2 = 3
    W3 = 5
    W4 = 7
    W5 = 11
    W6 = 23
    W7 = 11
    
    print(f"Thresholds: {T1} {T2} {T3} {T4} {T5} {T6}")
    print(f"Weights: {W1} {W2} {W3} {W4} {W5} {W6} {W7}")
    
    # 빈 배열을 원본과 동일한 크기로 생성
    scaled_map = np.zeros_like(height_map, dtype=float)
    
    mask1 = height_map < T1
    mask2 = (height_map >= T1) & (height_map < T2)
    mask3 = (height_map >= T2) & (height_map < T3)
    mask4 = (height_map >= T3) & (height_map < T4)
    mask5 = (height_map >= T4) & (height_map < T5)
    mask6 = (height_map >= T5) & (height_map < T6)
    mask7 = height_map >= T6

    # 스케일링 적용
    scaled_map[mask1] = height_map[mask1] * W1
    
    scaled_map[mask2] = (T1 * W1) + ((height_map[mask2] - T1) * W2)
    
    scaled_map[mask3] = (T1 * W1) + ((T2 - T1) * W2) + ((height_map[mask3] - T2) * W3)
    
    scaled_map[mask4] = (T1 * W1) + ((T2 - T1) * W2) + ((T3 - T2) * W3) + ((height_map[mask4] - T3) * W4)
    
    scaled_map[mask5] = (T1 * W1) + ((T2 - T1) * W2) + ((T3 - T2) * W3) + ((T4 - T3) * W4) + ((height_map[mask5] - T4) * W5)
    
    scaled_map[mask6] = (T1 * W1) + ((T2 - T1) * W2) + ((T3 - T2) * W3) + ((T4 - T3) * W4) + ((T5 - T4) * W5) + ((height_map[mask6] - T5) * W6)
    
    scaled_map[mask7] = (T1 * W1) + ((T2 - T1) * W2) + ((T3 - T2) * W3) + ((T4 - T3) * W4) + ((T5 - T4) * W5) + ((T6 - T5) * W6) + ((height_map[mask7] - T6) * W7)

    return scaled_map


def convert_range(pixels: np.array, old_min: float, old_max: float, new_min: float, new_max: float):
    return (pixels - old_min) / (old_max - old_min) * (new_max - new_min) + new_min

def double_height(image_path: str, output_path: str, as_16: bool = True):
    # 이미지 불러오기
    image = Image.open(image_path)
    
    if image.mode == 'RGBA':
        # 이미지를 그레이스케일로 변환
        image = image.convert('L')
        print("RGBA 이미지를 그레이스케일로 변환했습니다.")
    
    pixels = np.array(image).astype(np.uint16)
    print(f"before scaling: {np.min(pixels)} {np.max(pixels)}")
    new_pixels = apply_scaling(pixels)
    
    
    # 이미지 모드에 따른 처리
    if image.mode == 'L':  # 8비트 그레이스케일 (0-255)
        if as_16:
            new_pixels = convert_range(new_pixels, 0, np.max(new_pixels), MIN_HEIGHT_16, MAX_HEIGHT_16)
            new_pixels = new_pixels.astype(np.uint16)
            # 새로운 이미지 생성
            new_image = Image.fromarray(new_pixels, mode='I;16')
            print("이미지를 16비트로 변환하고 확대했습니다.")
        else:
            new_pixels = convert_range(new_pixels, 0, np.max(new_pixels), MIN_HEIGHT_8, MIN_HEIGHT_8)
            new_pixels = new_pixels.astype(np.uint8)
            new_image = Image.fromarray(new_pixels, mode='L')
            print("이미지를 8비트 상태에서 확대했습니다.")
    elif image.mode == 'I;16':  # 16비트 그레이스케일 (0-MAX_HEIGHT_16)
        new_pixels = convert_range(new_pixels, 0, np.max(new_pixels), MIN_HEIGHT_16, MAX_HEIGHT_16)
        new_image = Image.fromarray(new_pixels, mode='I;16')
    else:
        raise ValueError("지원하지 않는 이미지 모드입니다. 8비트 또는 16비트 그레이스케일 이미지만 처리할 수 있습니다.")
    
    # 새로운 이미지 저장
    new_image.save(output_path)


if __name__ == "__main__":
    config = configparser.ConfigParser()
    config.read('config.ini')
    
    height_map = config['DEFAULT']['height_map']
    
    output_path = os.path.join('./height_scale_output.png')

    before_image = Image.open(height_map)
    print(f"before height: {np.min(before_image)} {np.max(before_image)}")
    double_height(height_map, output_path)
    after_image = Image.open(output_path)
    print(f"after height: {np.min(after_image)} {np.max(after_image)}")
