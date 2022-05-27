# Version 1.1
## Features:
- The Pixar USD version has been updated to 21.11 with many new features, particularly enabling MaterialX in the OpenGL renderer.
- Support for Blender 3.1 and 3.2 has been added.
- Support for animated USD files has been added for final renders.  Furthermore, animated USD files can now be exported from Blender.
- Using Pixar’s RenderMan for final and viewport rendering is now supported. 

## Fixes:
- Support for the Film Transparent Background option for final renders has been added.
- The export process for instanced geometry has been accelerated.
- Materials could become orange if the user selected them in the viewport render — fixed.
- Fixed issues in the MaterialX editor:
    - An issue in the UI when linking nodes in the MaterialX editor has been eliminated;
    - Links between incompatible node sockets are not allowed anymore;
    - An issue with opening the MaterialX editor when a second window is open Has been fixed;
    - Errors if the MaterialX editor is open in the World mode or no objects are selected have been corrected.
- An issue which could lead to preview renders looping infinitely because of textures caching has been fixed.
- Wrong texture coordinates were applied with the OpenGL renderer — fixed.
- With the RPR Interactive mode, point lights could appear as cubes — fixed.
- Results when converting a Blender Principled node to Standard Surface have been improved.
- An issue in rendering scenes with empty material node trees has been fixed.
- Support for the Math shader node has been added.
- Errors when rendering the Animal Logic USD Lab scene have been fixed.
- Undo now works correctly with imported USD objects.
- Changing render modes with viewport rendering active now always updates the view.
- The environment light is now updated correctly when viewport rendering is active and an image is removed from the light color.
- Directional light now works correctly with OpenGL renders.


# Version 1.0

Version 1.0 of the Blender USD Hydra add-on has now been officially released.  This includes:


- Viewport and final rendering via Hydra using the hdStorm OpenGL renderer as well as one of the Radeon ProRender modes:
    - RPR Final — final rendering with the utmost physical correctness and image quality;
    - RPR Interactive — faster and more interactive viewport rendering using Vulkan ray-tracing.
- A nodegraph system for assembling and manipulating USD data. The assembled USD hierarchy is displayed in the Blender scene outline, even though USD data is not necessarily loaded into the Blender memory.  This allows the manipulation of USD data that is not fully loaded before the rendering time.
- Support for materials via the MaterialX system.  MaterialX nodes can be used to create materials, and native Blender materials can be converted to MaterialX.
- Integration with the new GPUOpen online MaterialX Material Library for loading example materials.
