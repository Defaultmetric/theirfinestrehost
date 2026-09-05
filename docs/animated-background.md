# Animated frontend background

Current source: Desktop/upscaled_germany3.mp4, 2560x1440, 60 fps, about 33.85 seconds.
Compared against Desktop/germany3.mp4 (1280x720) at 5, 16 and 28 seconds after
Lanczos conversion to 720p. The upscaled version was selected for cleaner contours
in the inspected samples; this is not a guarantee against all AI artifacts.

## Runtime format

- Exact displayed content resolution: 1280x720.
- 15 fps, 508 frames, 33.866666667-second loop (duration quantized to a frame).
- 64 screen cells, each 160x90 pixels, with two repeated bottom rows of padding.
- Each DXT1 atlas: 4000x1932, 25 columns x 21 rows of 160x92 tiles, no mipmaps.
- Padding aligns DXT1 compression blocks so adjacent animation frames do not share blocks.
- Shader UVs address the 160x90 content, excluding the padding. Unused final slots are not played.
- Texture total: 247,304,192 bytes (247.30 MB / 235.85 MiB).
- Previous version: 1248x704, 438 frames, 194.18 MB. Increase: 53.13 MB, primarily longer duration and full 720p.

The 60 fps source is sampled to 15 fps to preserve the existing storage/rendering
budget. The shader system does not play the source audio. DXT1 is lossy: quality
cannot be identical to the source. Three frames reconstructed from final DDS files
measured RGB PSNR 37.93, 37.63 and 38.08 dB versus uncompressed 720p references.
A reconstructed frame was visually checked. No in-game rendering test was run.

## Rebuild and validate

Run `python tools/build_menu_cinematic.py SOURCE.mp4 STAGING_DIRECTORY` with
FFmpeg/FFprobe on PATH and Pillow supporting DXT1 output. This generates textures
and metadata only; installing a different-duration source also requires updating
the shader frame count, loop, rows and atlas dimensions and validator dimensions.

Run `powershell -NoProfile -File tools/Test-AnimatedBackground.ps1` to check
package integrity, or pass `-ModRoot` for an installed copy. All 64 shaders and
textures must be shipped together. These atlases and the black parent texture
were missing from Git commit 87a5cd14; they are now included as local new files.

The animation is attached to frontend_background in interface/frontendmainview.gui.
It replaces the main-menu background, not the engine startup loading screens.
GUI cells use percentage sizes and shaders use normalized screen coordinates.
