import os
import shutil
import configparser

current_dir = os.path.dirname(os.path.abspath(__file__))

worlds_dir = os.path.join(current_dir, './temp-2')
output_dir = os.path.join(current_dir, './output')


###############################################################

# def load_world(path):
#     data = None
#     mca_path = os.path.join(path, 'region', 'r.0.0.mca')
#     with open(mca_path, mode='rb') as file:
#         data = file.read()
#     return anvil.Region(data)

# def create_new_world():
#     return anvil.EmptyRegion(0, 0)

# def save_world(world: anvil.EmptyRegion, path):
#     world.save(path)

# def merge_worlds(world: anvil.EmptyRegion, copy_world: anvil.Region, offset_x: int, offset_z: int, progress: Progress, chunk_task_id: TaskID):
#     width_blocks = TILE_WIDTH * SCALE_FACTOR
#     height_blocks = TILE_HEIGHT * SCALE_FACTOR

#     width_chunks = int(width_blocks // 16)
#     height_chunks = int(height_blocks // 16)
    
#     total_chunks = width_chunks * height_chunks
#     processed_chunks = 0

#     for x in range(width_chunks):
#         for z in range(height_chunks):
#             chunk = copy_world.get_chunk(x, z)
#             # i dont know but in world saving logic, it requires version
#             # setattr(chunk, 'version', 3337) # 1.19.4
#             world.add_chunk(chunk)
#             processed_chunks += 1
#             progress.update(chunk_task_id, completed=(processed_chunks / total_chunks) * 100)

#     return world

# def get_world_folders(base_path):
#     return [folder for folder in os.listdir(base_path) if folder.startswith("tile_")]

# def parse_offsets_from_folder_name(folder_name):
#     parts = folder_name.split('_')
#     width_offset = int(parts[2])
#     height_offset = int(parts[4])
#     return width_offset, height_offset

# def merge_all_worlds(base_path, output_path):
#     world_folders = get_world_folders(base_path)
    
#     base_world = create_new_world()
#     total_worlds = len(world_folders)
    
#     with Progress(
#         "[progress.description]{task.description}",
#         BarColumn(),
#         "[progress.percentage]{task.percentage:>3.1f}%",
#         "•",
#         TimeElapsedColumn(),
#     ) as progress:

#         # 모든 월드에 대한 전체 진행 상황
#         main_task = progress.add_task("[cyan]Merging all worlds...", total=total_worlds)

#         for folder in world_folders:
#             folder_path = os.path.join(base_path, folder, folder) # 폴더이름 한번 더 넣어야함
#             copy_world = load_world(folder_path)
#             width_offset, height_offset = parse_offsets_from_folder_name(folder)

#             # 각 월드를 병합할 때 청크별 진행 상황
#             chunk_task = progress.add_task(f"[green]Merging {folder} chunks...")

#             base_world = merge_worlds(base_world, copy_world, width_offset // 16, height_offset // 16, progress, chunk_task)  # 청크 단위로 오프셋 적용
            
#             progress.update(main_task, advance=1)  # 한 월드를 병합한 후 전체 진행도 업데이트
#             progress.remove_task(chunk_task)  # 청크 작업 완료 후 태스크 제거
    
#     save_world(base_world, output_path)
#     print(f"Merged world saved to {output_path}")

if __name__ == "__main__":
    config = configparser.ConfigParser()
    config.read('config.ini')

    wpscript_path = config['DEFAULT']['wpscript_path']
    tile_size = int(config['DEFAULT']['tile_size'])
    scale = int(config['DEFAULT']['scale'])

    # 월드 병합 실행
    shutil.rmtree(output_dir, ignore_errors=True)
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    merge_all_worlds(world_dir, output_mca)
