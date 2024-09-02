import os
import shutil
import threading
import subprocess
import glob
import time
from rich.progress import Progress, TimeElapsedColumn, BarColumn, TaskID

wpscript_path = "C:/Program Files/WorldPainter/wpscript.exe"

current_dir = os.path.dirname(os.path.abspath(__file__))

###############################################################


image_dir = os.path.join(current_dir, './temp-1')
output_dir = os.path.join(current_dir, './temp-2')

png_files = glob.glob(os.path.join(image_dir, 'tile_*.png'))

script_contents = ""
with open(os.path.join(current_dir, 'script.js'), 'r') as file:
    script_contents = file.read()


shutil.rmtree(output_dir, ignore_errors=True)
if not os.path.exists(output_dir):
    os.makedirs(output_dir)

def replace_params(script_contents, kwargs):
    for key, value in kwargs.items():
        script_contents = script_contents.replace('{{ param.' + key + ' }}', str(value))
    script_contents = script_contents.replace('\\', '/')
    return script_contents

def run_subprocess(command, progress: Progress, task_id: TaskID):
    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    
    # 프로세스 실행 중 진행 상황을 업데이트하는 함수
    start_time = time.time()
    def update_progress():
        while process.poll() is None:
            elapsed_time = time.time() - start_time
            progress.update(task_id, advance=elapsed_time * 0.1)
            time.sleep(0.1)  # 프로세스 진행도 업데이트 주기 설정

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


with Progress(
    "[progress.description]{task.description}",
    BarColumn(),
    "[progress.percentage]{task.percentage:>3.0f}%",
    TimeElapsedColumn(),
) as progress:
    # 전체 작업 진행도에 대한 태스크 생성
    main_task = progress.add_task("[cyan]Processing PNG files...", total=len(png_files))
    
    for png_file in png_files:
        _, tile_width, i, tile_height, j = os.path.splitext(os.path.basename(png_file))[0].split('_')
        world_path = os.path.join(output_dir, f'tile_{tile_width}_{i}_{tile_height}_{j}')
        if not os.path.exists(world_path):
            os.makedirs(world_path)

        script = replace_params(script_contents, {
            'heightmap_path': png_file,
            'world_path': world_path,
            'tile_width': tile_width,
            'tile_height': tile_height,
            'width_index': i,
            'height_index': j,
            'scale': 20,
            # 'scale': 5000,
        })
        
        temp_script_path = os.path.join(current_dir, 'script_temp.js')
        with open(temp_script_path, 'w') as file:
            file.write(script)
        
        # 각 서브프로세스에 대한 진행도 태스크 생성 (각 png_file에 대해)
        subprocess_task = progress.add_task(f"[green]Processing {os.path.basename(png_file)}...", total=100.0)

        # 서브프로세스를 실행하고, 해당 태스크 진행도를 관리
        run_subprocess([wpscript_path, temp_script_path], progress, subprocess_task)

        # 서브프로세스 완료 후 태스크 제거
        progress.remove_task(subprocess_task)
        shutil.rmtree(temp_script_path, ignore_errors=True)

        # 전체 작업 진행도 업데이트
        progress.update(main_task, advance=1)
