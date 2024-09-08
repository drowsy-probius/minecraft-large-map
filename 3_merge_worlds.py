import os
import signal
import shutil
import warnings
import multiprocessing
import glob
import time
from nbt import nbt
from nbt.region import RegionFile
from rich.progress import Progress

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
    shutil.copyfile(source_file, target_file)
    source_region = RegionFile(source_file)
    target_region = RegionFile(target_file)

    for x in range(32):
        for z in range(32):
            try:
                chunk = source_region.get_chunk(x, z)
            except Exception as e:
                warnings.warn(f"Failed to read chunk ({x}, {z}) from {source_file}: {e}")
                continue
            shifted_chunk = process_chunk(chunk, x_shift, z_shift)
            target_region.write_chunk(x, z, shifted_chunk)

    source_region.close()
    target_region.close()
    # print(f"Processed and created {remove_common_parent(source_file)} -> {remove_common_parent(target_file)}")

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

    with Progress() as progress:
        world_task = progress.add_task("[green]Processing worlds...", total=len(worlds))

        for world_folder in worlds:
            world_path = os.path.join(source_dir, world_folder)
            if not os.path.isdir(world_path):
                warnings.warn(f"Skipping {world_folder} as it is not a directory")
                progress.update(world_task, advance=1)
                continue

            size, x_offset, z_offset = get_world_info(os.path.basename(world_folder))
            region_folder = os.path.join(world_path, os.listdir(world_path)[0], 'region')

            if not os.path.exists(region_folder):
                warnings.warn(f"Skipping {world_folder} as it does not contain a region folder")
                progress.update(world_task, advance=1)
                continue

            mca_files = [f for f in os.listdir(region_folder) if f.endswith('.mca')]
            tasks = []
            for mca_file in mca_files:
                old_path = os.path.join(region_folder, mca_file)
                rx, rz = map(int, mca_file.split('.')[1:3])
                new_rx = rx + (x_offset // 512)
                new_rz = rz + (z_offset // 512)
                new_name = f'r.{new_rx}.{new_rz}.mca'
                new_path = os.path.join(target_dir, 'region', new_name)

                x_shift = x_offset // 16
                z_shift = z_offset // 16
                tasks.append((old_path, new_path, x_shift, z_shift))

            mca_task = progress.add_task(f"[cyan]Processing {remove_common_parent(world_folder)}...", total=len(tasks))
            with multiprocessing.Pool(processes=int(multiprocessing.cpu_count() * 0.8), initializer=init_worker) as pool:
                results = pool.starmap_async(process_mca_file, tasks)
                while not results.ready():
                    completed = results._number_left
                    progress.update(mca_task, completed=len(tasks) - completed)
                    time.sleep(0.1)

            progress.update(world_task, advance=1)
            progress.remove_task(mca_task)



if __name__ == "__main__":
    worlds_dir = os.path.join(current_dir, './temp-2')
    output_dir = os.path.join(current_dir, './output')

    if os.path.exists(output_dir):
        inp = input("Output directory already exists. Enter [remove] to delete it. else exit program and manually handle it: ")
        if inp.lower() == 'remove':
            shutil.rmtree(output_dir, ignore_errors=True)

    merge_worlds(worlds_dir, output_dir)
