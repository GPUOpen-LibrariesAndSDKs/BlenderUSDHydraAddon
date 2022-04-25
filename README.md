# Blender USD Hydra Addon

With Pixar's USD system emerging as a powerful tool for 3D graphics pipelines and interchange, this addon is meant to add first class support for USD and the USD Hydra rendering system to Blender. This allows:
- Importing USD files into Blender as "references". That USD file can be imported as part of the USD node tree, but not loaded into Blender's memory.
- Assembling Blender data and USD data to form a complex scene.
- Exporting assembled USD stages for use in other applications.
- Rendering in Blender via the USD Hydra Framework. This is a middle layer for renderers, meaning that once a renderer is adapted to Hydra, it can work in many places including this addon for rendering. Known Hydra render delegates are:
  - AMD's Radeon ProRender (included)
  - Hydra's default Storm delegate (included)
  - Pixar RenderMan delegate (included)  
  - Intel Embree (cpu) delegate
  - Autodesk Arnold
  - Otoy Octane
  - Redshift
  - Cycles
  - Intel Ospray
- Importing, exporting and editing materials using ILM's MaterialX standard.

In short, this addon will allow an artist or studio to assembled and compose USD data with Blender data, and render it all using various renderers via Hydra.

## Additional Documentation
- [Pixar USD](https://graphics.pixar.com/usd/docs/index.html)
- [Hydra](https://graphics.pixar.com/usd/docs/USD-Glossary.html#USDGlossary-Hydra)
- [MaterialX](http://www.materialx.org/)

## Requirements
Currently, this addon works only with [Blender 2.93+](https://www.blender.org/download/) in Windows and Linux. We hope to remove the restriction in the future, but there are a few things preventing this.

On the [releases](https://github.com/GPUOpen-LibrariesAndSDKs/BlenderUSDHydraAddon/releases) page are prebuilt versions of the addon. These include a copy of the USD library, as well as the Radeon ProRender Hydra delegate (under the directory `/libs-{python_version}`).

## Installing Add-on

Download the add-on from the releases page [releases](https://github.com/GPUOpen-LibrariesAndSDKs/BlenderUSDHydraAddon/releases). Open Blender preferences and got to the Add-ons section click Install button and pick the add-on in File Browser. Enable the add-on from the Add-ons section. 

>_WINDOWS USERS: Please note that old versions need to be disabled and uninstalled, and then Blender restarted. This is the case with many Blender addons that use C++ extensions: https://developer.blender.org/T77837_

For users who wish to install 3rd party render delegates (see above), they should be installed to the `libs-{python_version}/plugins/usd` directory in the addon folder similar to a regular USD installation.

## Usage
### Rendering
At a simple level, this functions similar to any render addon to Blender, like Cycles or EEVEE which are included in Blender. Simply select the render engine (in this case "USD Hydra") and render using the `F12` key or starting a viewport render. However, Hydra allows the added benefit of selecting a "Render Delegate". The default is using Radeon ProRender, AMD's cross device GPU path tracer.

Select a different render delegate in the render settings. Each render delegate may have it's own render settings.

### Assembling USD
By default, when rendering the plugin exports the Blender data to USD and passes through Hydra to the render delegate. This has the benefit of not having to write any renderer specific code for export.

However, more complex behavior is possible. Let's say you are animating a character in Blender and want to import a USD background scene that was created in another application. Normally these would be done via Blender's "linked libraries", but USD offers more powerful possibilities. Opening an editor window in Blender to the "USD" Nodegraph type will allow referencing in the background scene and merging with the Blender scene character for example.

### Materials via MaterialX
The correct way to interchange materials via USD is an open-ended question. The only built-in material nodes to USD are a simple USDPreviewSurface (very similar to Blender's Principled BSDF) and nodes to read textures. This is insufficient of course for complex materials. However, the MaterialX standard has emerged as a good interchange format for node-based materials with support from various applications such as Adobe Substance and various Autodesk Applications. Many renderers use their own nodes, but many can also support OSL shaders, which MaterialX can produce.

Therefore the material solution in the USD Hydra addon uses MaterialX. Here's a quick guide to materials:
- By default, when rendering any Blender materials with just Principled BSDF nodes will be converted automatically.
- There is a MaterialX based nodegraph available under the "MaterialX" editor.
- A handy conversion script is included to convert Blender Cycles nodegraphs to MaterialX (via the "Tools" panel in the material tab).
- MaterialX networks can be assembled in the editor (and exported for usage elsewhere).
- MaterialX networks from other applications can be imported here as well.

## Contributing
### Build Requirements
- [Blender 2.93+](https://www.blender.org/download/)
- [Python 3.9 x64](https://www.python.org/ftp/python/3.9.7/python-3.9.7-amd64.exe) _(Blender 2.93+ uses 3.9)_ or [Python 3.10 x64](https://www.python.org/ftp/python/3.10.2/python-3.10.2-amd64.exe) _(Blender 3.1+ uses 3.10)_
  - numpy - `pip install numpy`
  - requests - `pip install requests`
  - PyOpenGL - `pip install PyOpenGL`
  - PySide2 - `pip install PySide2`
  - jinja2 - `pip install jinja2`

- [Visual Studio 2019 Community](https://my.visualstudio.com/Downloads?q=visual%20studio%202017&wt.mc_id=o~msft~vscom~older-downloads) _(Windows only)_
- [CMake 3.22.2+](https://cmake.org/download/). Make sure it's added to the PATH environment variable

### Recommended software
- [epydoc](http://epydoc.sourceforge.net/) - enable PyCharm to parse Core's documentation. Use `py -m pip install epydoc` with your selected python interpreter or install it from PyCharm.
- [PyCharm Community Edition](https://www.jetbrains.com/pycharm/download/download-thanks.html?platform=windows&code=PCC) - recommended for coding, possible to enable intellisense(limited) for Blender code.
- [Visual Studio 2019 Community](https://visualstudio.microsoft.com/thank-you-downloading-visual-studio/?sku=Community&rel=16) - has a powerful python extension, possible to enable intellisense for Blender, provides remote debugging in Blender.

### Coding Conventions
Aim is to conform to [pep8](https://www.python.org/dev/peps/pep-0008/). 
At minimum it's 4 spaces for indentation, sources are utf-8, there's `.gitconfig` in the root of the project - please set you editor to use it (for most simplicity). PyCharm default setting are fine and seems that it also picks up `.editorconfig` automatically also, [Tortoise](https://tortoisegit.org/) Merge has a checkbox 'Enable EditorConfig', for Visual Studio there's [EditorConfig extension](https://visualstudiogallery.msdn.microsoft.com/c8bccfe2-650c-4b42-bc5c-845e21f96328).

### Git
We try to avoid merge commits, the easiest way to do it. This one rejects merges that would result in merge commit:
```commandline
> git config [--global] merge.ff only
```
Converts pull to do, essentially, fetch&rebase:
```commandline
> git config [--global] pull.rebase true
```
Also, make more meaningful commits (one commit per feature) the easy way. This will create a single change set from multiple commits coming from `<branch>`:
```commandline
> git merge <branch> --squash 
```

### ThirdParty libraries
There is ThirdParty repositories included to the project as a submodules. Please update submodules:
- `deps/USD` https://github.com/PixarAnimationStudios/USD
- `deps/HdRPR` https://github.com/GPUOpen-LibrariesAndSDKs/RadeonProRenderUSD

All of them are included via SSH protocol. You will need to create and install [SSH keys](https://help.github.com/en/github/authenticating-to-github/connecting-to-github-with-ssh).

Once SSH keys are installed update/checkout submodules for active branch:
```commandline
> git submodule update --init -f --recursive
```

### Build
Require `python 3.9+` to be set by default.

#### Windows:
Use Open x64 Native Tools Command Prompt for Visual Studio 2019 Community and run.
```commandline
> git clone https://github.com/GPUOpen-LibrariesAndSDKs/BlenderUSDHydraAddon
> cd BlenderUSDHydraAddon
> git submodule update --init --recursive
> python tools/build.py -all -bin-dir bin
```

#### Linux:
```commandline
> git clone https://github.com/GPUOpen-LibrariesAndSDKs/BlenderUSDHydraAddon
> cd BlenderUSDHydraAddon
> git submodule update --init --recursive
> python tools/build.py -all -bin-dir bin
```

For building on non-default system python version you should change it with `update-alternatives --config python` command or via setting venv.

#### Build tool
You can build project using `tools/build.py` with different flag combinations. It allows you to create a folder with binaries and copy all the necessary files for development to `/libs-{python_version}` folder. Also `tools/build.py` provides a verity of ways to make a project builds:
- `-all` - builds all binaries, equals to `-usd -hdrpr -libs -mx-classes -addon` 
- `-usd` - builds usd binaries
- `-hdrpr` - builds HdRPR plugin binaries
- `-bin-dir <bin dir>` - define folder to build binaries
- `-libs` - copies all the necessary for development libraries to `lib-{python_version}` folder, needs to be passed with `-usd`, `-hdrpr`
- `-clean` - removes binaries folder before build, for example: `-all -clean ...` remove all folders in `<bin dir>`, `-usd -hdrpr -clean` removes only `<bin dir>/Usd` and `<bin dir>/HdRPR`
- `-mx-classes` - generates classes for MaterialX nodes
- `-G "Visual Studio 16 2019"` - set builder, passing with `-all` and `-hdrpr` _(Windows only)_ 
- `-addon` - generates zip archive with plugin to `/install` folder. Resulted build writes python version to zipped file (i.e., {archive_name}-3.10.zip);
- `--prman` - build with RenderMan delegate
- `--prman-location` - path to RenderMan directory (e.g. 'C:/Program Files/Pixar/RenderManProServer-24.3')

To build addon with RenderMan you need to install RenderMan first (https://renderman.pixar.com/install) and then set environment variables according to instruction [Running hdPrman](https://graphics.pixar.com/usd/release/plugins_renderman.html#running-hdprman)  

Arguments are mostly used to skip build unneeded binaries. For example, you want switch to prebuild binary folder `bin/dir_01`:
```commandline
> python tools/build.py -libs -mx-classes -bin-dir bin/dir_01
```
### Debugging
#### Visual Studio 2019
Recommended software for debugging, has really nice mixed python and C stack debugging. Provides to you ability of interactive code evaluation. You can make breakpoints move step by step, watch variables and etc.

##### 1. Run Blender with the Add-on
Make sure you have no installed addon for Blender version you want to use; remove installed version if needed.

```commandline
> set BLENDER_EXE="C:\Program Files\Blender Foundation\Blender 2.93\blender.exe"
> python tools\run_blender_test_addon.py --window-geometry 0 0 1920 1080
```

##### 2. Attach Visual Studio to process
Press menu Debug -> Attach to Process... or use hotkey`Ctrl+Alt+P`. In opened window choose Blender process, now you connected and allowed to debug.
Also use build-in Python debugger in realtime. Turn on with `Debug -> Windows -> Python Debug Interactive. 

#### Blender
 The easiest way to [build Blender](https://wiki.blender.org/wiki/Building_Blender/Windows) in Release or RelWithDebInfo and add `#pragma optimize( "", off )`.

#### PyCharm
```python
import pydevd
pydevd.settrace('localhost', port=52128, stdoutToServer=True, stderrToServer=True, suspend=False)
```

### Logging
Using python's `logging` module underneath, hdusd.utils.logging has functions similar to logging. It also includes callable class Log which provides simplified interface to do logging.

##### Code example:
```python
from hdusd.utils import logging
log = logging.Log(tag='export.mesh')

log("sync", mesh, obj)
```
For example, `logging.debug(*argv, tag)` where argv is what is printed (same as with print) and tag is string suffix for logger name, for filtering, so that `logging.limit_log(name, level_show_always)` will allow to filter out what doesn't start with `name`(expect levels equal or above `level_show_always`).

Configure your session `configdev.py` (loaded very early) can be used to include code like `limit_log`.

##### configdev.py example:
```python
from .utils import logging
logging.limit_log('default', logging.DEBUG) # set debug level

from . import config
config.engine_use_preview = False # turn off preview of materials
```
