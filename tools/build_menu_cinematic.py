"""Build 720p / 15fps menu DDS atlases in a staging folder (Pillow + FFmpeg)."""
import argparse
import json
import math
import subprocess
from pathlib import Path
from PIL import Image

p = argparse.ArgumentParser(description=__doc__)
p.add_argument('source', type=Path)
p.add_argument('output', type=Path)
a = p.parse_args()
a.output.mkdir(parents=True, exist_ok=True)
# 160x90 screen cells; pad to a 160x92 BC1 block-aligned tile so compressed
# blocks never mix pixels from different animation frames.
cols, fps = 25, 15
probe = json.loads(subprocess.check_output(['ffprobe', '-v', 'error', '-select_streams', 'v:0',
    '-show_entries', 'stream=duration,width,height', '-of', 'json', str(a.source)]))['streams'][0]
capacity = math.ceil(float(probe['duration']) * fps) + 1
rows = math.ceil(capacity / cols)
assert rows * 92 <= 4096
atlases = [Image.new('RGB', (cols*160, rows*92)) for _ in range(64)]
proc = subprocess.Popen(['ffmpeg', '-v', 'error', '-i', str(a.source), '-an',
    '-vf', 'fps=15,scale=1280:720:flags=lanczos', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-'], stdout=subprocess.PIPE)
n = 0
size = 1280*720*3
while True:
    data = proc.stdout.read(size)
    if not data:
        break
    assert len(data) == size, 'Truncated raw frame'
    assert n < cols*rows
    frame = Image.frombytes('RGB', (1280,720), data)
    x, y = n % cols * 160, n // cols * 92
    for i, atlas in enumerate(atlases):
        cx, cy = i % 8 * 160, i // 8 * 90
        tile = frame.crop((cx,cy,cx+160,cy+90))
        atlas.paste(tile, (x,y))
        atlas.paste(tile.crop((0,89,160,90)).resize((160,2)), (x,y+90))
    if n in (75,240,420):
        frame.save(a.output/f'reference-{n}.png')
    n += 1
assert proc.wait() == 0 and n > 0
for i,atlas in enumerate(atlases):
    atlas.save(a.output/f'tfr_c{i:02}.dds',pixel_format='DXT1')
meta = dict(source=str(a.source), width=1280, height=720, fps=fps, frames=n,
            loop=n/fps, cols=cols, rows=rows, atlas_width=cols*160, atlas_height=rows*92,
            tile_width=160, tile_height=92, content_width=160, content_height=90)
(a.output/'cinematic.json').write_text(json.dumps(meta,indent=2)+'\n')
print(json.dumps(meta),flush=True)
