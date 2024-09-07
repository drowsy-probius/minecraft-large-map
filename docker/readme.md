example

```
docker run --rm \
  --memory 96g \
  --memory-swap 118g \
  -v /host/resource/dir:/data \
  -v ./wpscript.vmoptions:/opt/worldpainter/wpscript.vmoptions \
  /data/your_script.js
```
