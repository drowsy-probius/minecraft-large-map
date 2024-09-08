import os
import signal
import shutil
import configparser
import warnings
import multiprocessing
import glob
from nbt import nbt
from nbt.region import RegionFile

current_dir = os.path.dirname(os.path.abspath(__file__))

def remove_common_parent(path: os.PathLike):
    return os.path.relpath(path, start=current_dir)

###############################################################

def init_worker():
    signal.signal(signal.SIGINT, signal.SIG_IGN)

def get_world_info(folder_name):
    parts = folder_name.split('_')
    size = int(parts[1])
    x_offset = int(parts[2])
    z_offset = int(parts[3])
    return size, x_offset, z_offset

def shift_coordinates(tag, x_shift, z_shift):
    if isinstance(tag, nbt.TAG_Compound):
        for key, value in tag.items():
            if key in ['x', 'X']:
                tag[key] = nbt.TAG_Int(value.value + x_shift)
            elif key in ['z', 'Z']:
                tag[key] = nbt.TAG_Int(value.value + z_shift)
            elif isinstance(value, (nbt.TAG_List, nbt.TAG_Compound)):
                shift_coordinates(value, x_shift, z_shift)
    elif isinstance(tag, nbt.TAG_List):
        for item in tag:
            shift_coordinates(item, x_shift, z_shift)

def process_chunk(chunk, x_shift, z_shift):
    chunk['xPos'] = nbt.TAG_Int(chunk['xPos'].value + x_shift)
    chunk['zPos'] = nbt.TAG_Int(chunk['zPos'].value + z_shift)
    shift_coordinates(chunk, x_shift * 16, z_shift * 16)
    return chunk

def process_mca_file(source_file, target_file, x_shift, z_shift):
    print(f"Processing {remove_common_parent(source_file)}")
    shutil.copyfile(source_file, target_file)
    source_region = RegionFile(source_file)
    target_region = RegionFile(target_file)

    for x in range(32):
        for z in range(32):
            chunk = source_region.get_chunk(x, z)
            if chunk is None:
                warnings.warn(f"Chunk ({x}, {z}) is missing in {source_file}")
                continue
            shifted_chunk = process_chunk(chunk, x_shift, z_shift)
            target_region.write_chunk(x, z, shifted_chunk)

    source_region.close()
    target_region.close()
    print(f"Processed and created {remove_common_parent(source_file)} -> {remove_common_parent(target_file)}")
    

def merge_worlds(source_dir, target_dir):
    if not os.path.exists(target_dir):
        os.makedirs(target_dir)
    os.makedirs(os.path.join(target_dir, 'region'), exist_ok=True)
    os.makedirs(os.path.join(target_dir, 'datapacks'), exist_ok=True)
    os.makedirs(os.path.join(target_dir, 'entities'), exist_ok=True)

    worlds = glob.glob(os.path.join(source_dir, 'tile_[0-9]*_[0-9]*_[0-9]*'))
    tasks = []
    worlds = [(world, *(os.path.basename(world).split('_')[1:])) for world in worlds]
    worlds = sorted(worlds, key=lambda x: (int(x[1]), int(x[2]), int(x[3])))
    worlds = [world[0] for world in worlds]

    # Copy level.dat from the first world
    first_world = worlds[0]
    first_subworld = os.path.join(first_world, os.listdir(first_world)[0])
    level_dat_path = os.path.join(first_subworld, 'level.dat')
    if os.path.exists(level_dat_path):
        shutil.copy2(level_dat_path, os.path.join(target_dir, 'level.dat'))
        print("Copied level.dat from the first world")

    for world_folder in worlds:
        world_path = os.path.join(source_dir, world_folder)
        if not os.path.isdir(world_path):
            warnings.warn(f"Skipping {world_folder} as it is not a directory")
            continue
        
        size, x_offset, z_offset = get_world_info(world_folder)
        region_folder = os.path.join(world_path, os.listdir(world_path)[0], 'region')
        
        if not os.path.exists(region_folder):
            warnings.warn(f"Skipping {world_folder} as it does not contain a region folder")
            continue
        
        for mca_file in os.listdir(region_folder):
            if not mca_file.endswith('.mca'):
                warnings.warn(f"Skipping {mca_file} as it is not an MCA file")
                continue
            
            old_path = os.path.join(region_folder, mca_file)
            rx, rz = map(int, mca_file[2:-4].split('.'))
            rx, rz = map(int, mca_file.split('.')[1:3])
            new_rx = rx + (x_offset // 512)
            new_rz = rz + (z_offset // 512)
            new_name = f'r.{new_rx}.{new_rz}.mca'
            new_path = os.path.join(target_dir, 'region', new_name)
            
            x_shift = x_offset // 16
            z_shift = z_offset // 16
            tasks.append((old_path, new_path, x_shift, z_shift))

    with multiprocessing.Pool(initializer=init_worker) as pool:
        pool.starmap(process_mca_file, tasks)



if __name__ == "__main__":
    config = configparser.ConfigParser()
    config.read('config.ini')

    wpscript_path = config['DEFAULT']['wpscript_path']
    tile_size = int(config['DEFAULT']['tile_size'])
    scale = int(config['DEFAULT']['scale'])

    worlds_dir = os.path.join(current_dir, './temp-2')
    output_dir = os.path.join(current_dir, './output')

    if os.path.exists(output_dir):
        inp = input("Output directory already exists. Enter [remove] to delete it. else exit program and manually handle it: ")
        if inp.lower() == 'remove':
            shutil.rmtree(output_dir, ignore_errors=True)

    merge_worlds(worlds_dir, output_dir)
