거대한 마인크래프트 맵을 height map으로부터 생성합니다.

> ! 상대적으로 작은 크기에서 테스트가 진행되었고 모든 경우에서의 정상 동작을 보장하지 않습니다.

> ! 완성될 맵의 크기에 따라 매우 많은 시간과 저장 공간이 필요합니다.

# 요구 사항

- worldpainter
- python 3.12
- 기초 터미널 사용법
- 기초 파이썬 지식

# 실행 방법

## 1.사전 준비

### `config.ini` 작성

- wpscript_path

  > worldpainter가 설치된 폴더의 `wpscript.exe` 파일의 경로를 입력합니다.

- height_map

  > 마인크래프트 맵으로 변환할 height map의 경로를 지정합니다.

- tile_size

  > 분할될 height map 조각 이미지의 가로 세로 픽셀 크기입니다.

- scale
  > 분할된 height map 이 마인크래프트 월드로 변환 된 후 조정될 비율입니다. worldpainter에서 사용됩니다.

> height map의 가로 세로 길이가 512의 배수가 아닐 경우에 빈 공간은 height map의 값 0으로 보간됩니다.

### `config.ini` 예시

```ini
[DEFAULT]
wpscript_path=C:\Program Files\WorldPainter\wpscript.exe

height_map=./images/heightmap.png
tile_size=256
scale=1000
```

### `script.js` 파일 수정

큰 크기의 height map을 먼저 적용하기 전에 작은 크기의 height map을 worldpainter에서 불러오면서 값을 설정해야합니다.

설정해야 할 값은 다음과 같습니다.

- water level (`withWaterLevel(6)`)
- height low, height mapping (`.fromLevels(0, 65535).toLevels(0, 768)`)
- build limit (`.withLowerBuildLimit(-512).withUpperBuildLimit(1024)`)

위 값 중 특히 water level 값은 height map마다 다르므로 직접 눈으로 확인해가며 설정해야합니다.

`{{ param.asdf }}` 형식의 부분은 수정 시에 제대로 동작하지 않을 수 있습니다.

### `script.js` 예시

```javascript
var heightMap = wp.getHeightMap()
  .fromFile('{{ param.heightmap_path }}')
  .go();
print("get height map done.")

var mapFormat = wp.getMapFormat()
  .withId('org.pepsoft.anvil.1.19')
  .go();
print("get map format done.")


// withLowerBuildLimit 0 -64 -128 -256 -512 -1024 -2032
// withUpperBuildLimit 256 320 512 1024 1536 2032
// default? -64 320
var world = wp.createWorld()
  .fromHeightMap(heightMap)
  .scale({{ param.scale }})
  .shift(0, 0)
  .fromLevels(0, 65535).toLevels(0, 768)
  .withWaterLevel(6)
  .withMapFormat(mapFormat)
  .withLowerBuildLimit(-512)
  .withUpperBuildLimit(1024)
  .go();
print("create world done.")

// wp.saveWorld(world)
//   .toFile('{{ param.world_path }}')
//   .go();

wp.exportWorld(world)
  .toDirectory('{{ param.world_path }}')
  .go();

print("save world done.")
```

## 2. (optional) height map 값 보정

```bash
python 0_stretch_height_map.py
```

사용할 height map 의 값의 범위를 조정할 때 사용합니다. 낮은 값에는 작은 가중치를 높은 값에는 높은 가중치를 곱하여 더욱 극적인 월드를 생성할 수 있습니다.

모든 height map에 적합한 설정 값은 없으며 분할하기 전 작은 height map에 적용한 후 worldpainter gui에서 결과를 확인하며 사용하는게 좋습니다.

가중치를 변경하려면 `0_stretch_height_map.py`의 `apply_scaling` 함수를 변경할 수 있습니다.

## 3. 거대한 height map을 여러 개의 조각으로 분할

```bash
python 1_split_height_map.py
```

큰 height map의 이미지를 `config.ini`에 설정한 tile 값으로 분할합니다.

분할된 이미지는 `cwd`의 `temp-1` 디렉토리에 저장됩니다. 저장된 이미지 형식은 `tile_{tile_pixel_size}_{x_offset}_{z_offset}.png` 입니다.

## 4. 각각의 height map 조각을 마인크래프트 맵으로 변환

```bash
python 2_height_map_to_world.py
```

`temp-1` 디렉토리에 저장된 height map 타일 이미지 각각을 `config.ini`에 설정한 scale을 사용하여 마인크래프트 월드 형식으로 변환합니다. 이 때 사용되는 스크립트는 프로젝트 루트의 `script.js`를 사용합니다.

변환된 마인크래프트 월드는 `temp-2` 폴더에 저장됩니다. 저장된 마인크래프트 월드의 폴더명은 `tile_{tile_world_size}_{x_offset}_{z_offset}` 입니다.

연산이 완료된 이미지는 파일명 앞에 `done_` 접두사가 붙으며 스크립트를 다시 실행하더라도 중복된 연산을 하지 않도록 되어있습니다.

하나의 타일의 변환이 진행 중일 때 `Out Of Memory` 에러가 발생하더라도 파이썬 스크립트 자체는 종료되지 않습니다. 그러므로 하나의 타일이 메모리 오류 없이 변환되는지 확인이 필요합니다.

> 13600k CPU에서 tile_size 256, scale 1000일 때 하나의 타일을 처리하는데 대략 5분이 소요되었습니다. 하나의 타일을 처리할 때 사용된 메모리는 60GB 이상으로 추정됩니다.

## 5. 마인크래프트 월드 파일 (.mca)를 병합

```bash
python 3_merge_worlds.py
```

`temp-2` 폴더의 마인크래프트 월드에 대해서 하나의 마인크래프트 월드로 병합을 진행합니다. 폴더 내의 제일 처음 월드에서 `level.dat` 파일을 복사합니다.

각 타일 월드는 폴더명으로부터 병합된 월드에서의 위치를 계산합니다. 따라서 `temp-2` 폴더 내의 파일명을 변경했다면 정상적으로 동작하지 않을 수 있습니다.

이 작업은 각 타일 간의 의존성이 없으므로 전체 cpu 코어의 80%를 사용하여 병렬 처리를 수행합니다. 메모리 사용량은 상대적으로 적습니다.

병합이 완료된 월드는 `output` 디렉토리에 저장됩니다. 저장된 월드는 게임에서 바로 불러올 수 있습니다.
