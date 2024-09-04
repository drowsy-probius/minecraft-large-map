import os
import shutil
import threading
import subprocess
import glob
import time
import configparser
from rich.progress import Progress, TimeElapsedColumn, BarColumn, TaskID

current_dir = os.path.dirname(os.path.abspath(__file__))

###############################################################

image_dir = os.path.join(current_dir, './temp-1')
output_dir = os.path.join(current_dir, './temp-2')

script_contents = ""

def replace_params(script_contents, kwargs):
    for key, value in kwargs.items():
        script_contents = script_contents.replace('{{ param.' + key + ' }}', str(value))
    script_contents = script_contents.replace('\\', '/')
    return script_contents

def run_subprocess(command, progress: Progress, task_id: TaskID):
    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    
    # 프로세스 실행 중 진행 상황을 업데이트하는 함수
    def update_progress():
        while process.poll() is None:
            progress.update(task_id)
            time.sleep(0.5)  # 프로세스 진행도 업데이트 주기 설정

    # stdout 출력 스레드
    def handle_stdout(stdout):
        for line in iter(stdout.readline, b''):
            if line:
                print(line.decode().strip())
        stdout.close()
    
    # stderr 출력 스레드
    def handle_stderr(stderr):
        for line in iter(stderr.readline, b''):
            if line:
                print(line.decode().strip())
        stderr.close()

    # 각각의 스레드 시작
    stdout_thread = threading.Thread(target=handle_stdout, args=(process.stdout,))
    stderr_thread = threading.Thread(target=handle_stderr, args=(process.stderr,))
    
    stdout_thread.start()
    stderr_thread.start()

    # 프로세스 진행 상태를 업데이트하는 스레드 시작
    progress_thread = threading.Thread(target=update_progress)
    progress_thread.start()
    
    # 프로세스가 끝날 때까지 대기
    process.wait()
    progress.update(task_id, advance=100)

    # 모든 스레드가 끝날 때까지 대기
    stdout_thread.join()
    stderr_thread.join()
    progress_thread.join()

def convert_to_worlds(wpscript_path: str, tile_size: int, scale: int, png_files: list):
    scale_ratio = scale / 100

    with Progress(
        "[progress.description]{task.description}",
        BarColumn(),
        "[progress.percentage]{task.percentage:>3.0f}%",
        TimeElapsedColumn(),
    ) as progress:
        # 전체 작업 진행도에 대한 태스크 생성
        main_task = progress.add_task("[cyan]Processing PNG files...", total=len(png_files))
        
        for png_file in png_files:
            _, file_tile_size, x_offset, z_offset = os.path.splitext(os.path.basename(png_file))[0].split('_')
            if file_tile_size != str(tile_size):
                progress.update(main_task, advance=1)
                print(f"Tile size mismatch: {file_tile_size} != {tile_size}. Skipping {png_file}")
                continue

            x_offset = int(x_offset)
            z_offset = int(z_offset)
            
            block_size = int(tile_size * scale_ratio)
            block_offset_x = int(x_offset * scale_ratio)
            block_offset_z = int(z_offset * scale_ratio)
            
            world_path = os.path.join(output_dir, f'tile_{block_size}_{block_offset_x}_{block_offset_z}')
            if not os.path.exists(world_path):
                os.makedirs(world_path)

            script = replace_params(script_contents, {
                'heightmap_path': png_file,
                'world_path': world_path,
                'scale': scale, 
            })
            
            temp_script_path = os.path.join(current_dir, 'script_temp.js')
            with open(temp_script_path, 'w') as file:
                file.write(script)
            
            # 각 서브프로세스에 대한 진행도 태스크 생성 (각 png_file에 대해)
            subprocess_task = progress.add_task(f"[green]Processing {os.path.basename(png_file)}...", total=None)

            # 서브프로세스를 실행하고, 해당 태스크 진행도를 관리
            run_subprocess([wpscript_path, temp_script_path], progress, subprocess_task)

            # 서브프로세스 완료 후 태스크 제거
            progress.remove_task(subprocess_task)
            shutil.rmtree(temp_script_path, ignore_errors=True)

            # 전체 작업 진행도 업데이트
            progress.update(main_task, advance=1)

if __name__ == "__main__":
    config = configparser.ConfigParser()
    config.read('config.ini')

    wpscript_path = config['DEFAULT']['wpscript_path']
    tile_size = int(config['DEFAULT']['tile_size'])
    scale = int(config['DEFAULT']['scale'])

    png_files = glob.glob(os.path.join(image_dir, 'tile_*.png'))
    
    with open(os.path.join(current_dir, 'script.js'), 'r') as file:
        script_contents = file.read()

    shutil.rmtree(output_dir, ignore_errors=True)
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    convert_to_worlds(wpscript_path, tile_size, scale, png_files)
