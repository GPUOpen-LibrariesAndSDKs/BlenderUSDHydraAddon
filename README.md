# Blender USD Hydra Addon

With Pixar's USD system emerging as a powerful tool for 3D graphics pipelines and interchange, this addon is meant to add first class support for USD and the USD Hydra rendering system to Blender.  This allows:
- Importing USD files into Blender as "references". That is a USD file can be imported as part of the scenegraph, but not loaded into Blender's memory.
- Assembling Blender data and USD data to form a complex scene.
- Exporting assembled USD stages for use in other applications
- Rendering in Blender via the USD Hydra Framework.  This is a middle layer for renderers, meaning that once a renderer is adapted to Hydra, it can work in many places including this addon for rendering.  Known Hydra render delegates are:
  - AMD's Radeon ProRender (included)
  - Hydra's default Storm delegate (included)
  - Intel Embree (cpu) delegate
  - Pixar RenderMan delegate.
  - Autodesk Arnold
  - Otoy Octane
  - Redshift
  - Cycles
  - Intel Ospray
- Importing, exporting and editing materials using ILM's MaterialX standard (TODO)

In short, this addon will allow an artist or studio to assembled and compose USD data with Blender data, and render it all using various renderers via Hydra

## Further reading
- Pixar USD https://graphics.pixar.com/usd/docs/index.html
- Hydra https://graphics.pixar.com/usd/docs/USD-Glossary.html#USDGlossary-Hydra
- MaterialX http://www.materialx.org/

## Requirements
Currently, this addon works only with Blender 2.90+ and only in Windows.  We hope to remove the restriction in the future, but there are a few things preventing this.  In particular, the current build of Blender has USD statically linked in, which the addon cannot access.  https://developer.blender.org/T76490

On the releases page [LINK NEEDED] are prebuilt versions of the addon.  These include a copy of the USD library (under the directory "usd"), as well as the Radeon ProRender Hydra delegate.  If building from source, a local version of the USD library is required.  Point to this with the USD_ROOT environment variable.

## Installing

Simply download a build from the releases page [LINK NEEDED] and install via the Blender addons in Edit->System Preferences menu.  
WINDOWS USERS:  Please note that old versions need to be disabled and uninstalled, and then Blender restarted.  This is the case with many Blender addons that use C++ extenstions:  https://developer.blender.org/T77837

For users who wish to install 3rd party render delegates (see above), they should be installed to the "usd/plugins" directory in the addon folder similar to a regular USD installation.

## Usage
### Rendering
At a simple level, this functions similar to any render addon to Blender, like Cycles or EEVEE which are included in Blender.  Simply select the render engine (in this case "USD Hydra") and render using the F12 key or starting a viewport render.  However, Hydra allows the added benefit of selecting a "Render Delegate".  The default is using Radeon ProRender, AMD's cross device GPU path tracer.

Select a different render delegate in the render settings.  Each render delegate may have it's own render settings

### Assembling USD
By default, when rendering the plugin exports the Blender data to USD and passes through Hydra to the render delegate.  This has the benefit of not having to write any renderer specific code for export.

However, more complex behavior is possible.  Let's say you are animating a character in Blender and want to import a USD background scene that was created in another application.  Normally these would be done via Blender's "linked libraries", but USD offers more powerful possibilities.  Opening an editor window in Blender to the "USD Nodegraph" type will allow referencing in the background scene and merging with the Blender scene character for example.

[picture]

The possibilities here are endless, to read more, look at our documentation on the various nodes available [HERE]


### Materials via MaterialX (TODO)
The correct way to interchange materials via USD is an open-ended question.  The only built-in material nodes to USD are a simple USDPreviewSurface (very similar to Blender's Principled BSDF) and nodes to read textures.  This is insufficient of course for complex materials.  However, the MaterialX standard has emerged as a good interchange format for node-based materials with support from various applications such as Adobe Substance and various Autodesk Applications.  Many renderers use their own nodes, but many can also support OSL shaders, which MaterialX can produce.

Therefore the material solution in the USD Hydra addon uses MaterialX.  Here's a quick guide to materials:
- By default, when rendering any Blender materials with just Principled BSDF nodes will be converted automatically
- There is a MaterialX based nodegraph available under the "USD MaterialX" editor.  
- A handy conversion script is included to convert Blender Cycles nodegraphs to MaterialX (Via the "Convert Material" button in the material tab)
- MaterialX networks can be assembled in the editor (and exported for usage elsewhere).
- MaterialX networks from other applications can be imported here as well.

## Developing

### Coding Conventions

Aim is to conform to [pep8](https://www.python.org/dev/peps/pep-0008/). 
At minimum it's 4 spaces for indentation, sources are utf-8, there's .gitconfig in the root of the project - please set you editor to use it(for most simplicity). E.g. PyCharm(recommended!) default setting are fine and seems that it also picks up .editorconfig automatically also, Tortoise Merge has a checkbox 'Enable EditorConfig', for Visual Studio there's [EditorConfig extension](https://visualstudiogallery.msdn.microsoft.com/c8bccfe2-650c-4b42-bc5c-845e21f96328)

Git - we try to avoid merge commits, easiest way to do it:

`git config [--global] merge.ff only` # this one rejects merges that would result in merge commit
 
`git config [--global] pull.rebase true` # converts pull to do, essentially, fetch&rebase 

Also, make more meaningful commits(one commit per feature) the easy way: 

`git merge <branch> --squash` # this will create a single change set from multiple commits coming from <branch>

### Recommended software

- epydoc - enable PyCharm to parse Core's documentation. Use `py -m pip install epydoc` with your selected python interpreter or install it from PyCharm 
- PyCharm Community Edition - very recommended, possible to enable intellisense(limited) for Blender code and for RPR Core
- Visual Studio Code - has a very nice python extension, possible to enable intellisense for Blender and for RPR Core, provides remote debugging in Blender

## Build


## Run Addon while developing it(without real installation)

- make sure you have no installed addon for Blender version you want to use; remove installed version if needed.
- set environment variable BLENDER_EXE to blender.exe you want to use via the command line or system environment settings.
- run run_blender_with_rpr.cmd

Example:

`set BLENDER_EXE="C:\Program Files\Blender Foundation\Blender 2.90\blender.exe" && run_blender_with_rpr.cmd`

### Debugging

#### log

Using python's 'logging' module underneath, hdusd.utils.logging has functions similar to logging. It also includes callable class Log which provides simplified interface to do logging.
Example:
    from hdusd.utils import logging
    log = logging.Log(tag='export.mesh')

    log("sync", mesh, obj)

e.g. `logging.debug(*argv, tag)` where argv is what is printed(same as with print) and tag is string suffix for logger name, for filtering
so that `logging.limit_log(name, level_show_always)` will allow to filter out what doesn't start with `name`(expect levels equal or above `level_show_always`)

 configdev.py(loaded very early) can be used to include code like `limit_log` to configure your session

    from .utils import logging
    logging.limit_log('default', logging.DEBUG)
    
    from . import config
    config.pyrpr_log_calls = True #  log all Core function calls to console, can be VERY useful

- Visual Studio has really nice(and working) mixed(python and C stack) debugging - recommended! 
- Blender debug - it's easiest to [build Blender](https://wiki.blender.org/index.php/Dev:Doc/Building_Blender/Windows/msvc/CMake) in Release or RelWithDebInfo(and add ``#pragma optimize( "", off )``) 
- Debug in PyCharm - `import pydevd; pydevd.settrace('localhost', port=52128, stdoutToServer=True, stderrToServer=True, suspend=False)`

## Making a new release

- run `build_installer.py <build_folder>`. Where `build_folder` is some separate location - it will clone needed repos(if not already), reset then to needed branch and build installer. Byt default it builds windows installer on master.  
- tag the commit in the build folder's ProRenderBlenderPlugin `git tag builds/x.y.zz`
- push the tag `git push --tags` 
- increase version in `src/hdusd/__init__.py`

## PyCharm

### Blender api intellisense support

Get [pycharm-blender](https://github.com/mutantbob/pycharm-blender). See instructions on the github page or, in short, 
run `pypredef_gen.py` from Blender itself or using command line, e.g. `blender --python pypredef_gen.py`,
add "pypredef" folder path that this script creates to you PyCharm Interpreter paths, find paths settings under `File | Settings(or Default Settings) | Project Interpreter`
 
Increase max file size for Pycharm intellisence(bpy.py generated is huge), go to `Help | Edit Custom VM Options` and add the following line:

  -Didea.max.intellisense.filesize=5000000

Restart PyCharm

## Visual Studio Code

#### Install Blender-VScode-Debugger addon

#### Attach VS remote debugger to Blender

 

### Versioning

The version number should be updated when a new plugin is released.  This is done by editing the version field
of the bl_info structure in the src/hdusd/__init__.py file. Currently a build script will update the build
number when checkins happen to the master branch.  So it is only necessary to update the major or minor number
when required.

