# Version 1.0

Version 1.0 of the Blender USD Hydra add-on has now been officially released.  This includes:


- Viewport and final rendering via Hydra using the hdStorm OpenGL renderer as well as one of the Radeon ProRender modes:
    - RPR Final — final rendering with the utmost physical correctness and image quality;
    - RPR Interactive — faster and more interactive viewport rendering using Vulkan ray-tracing.
- A nodegraph system for assembling and manipulating USD data. The assembled USD hierarchy is displayed in the Blender scene outline, even though USD data is not necessarily loaded into the Blender memory.  This allows the manipulation of USD data that is not fully loaded before the rendering time.
- Support for materials via the MaterialX system.  MaterialX nodes can be used to create materials, and native Blender materials can be converted to MaterialX.
- Integration with the new GPUOpen online MaterialX Material Library for loading example materials.
