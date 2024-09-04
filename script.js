/**
 * param
 *   heightmap_path: string
 *   world_path: string
 *   scale: int
 *   tile_width: int
 *   tile_height: int
 *   width_index: int
 *   height_index: int
 */

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
