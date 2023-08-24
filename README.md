# Blender USD Hydra Addon

With Pixar's USD system emerging as a powerful tool for 3D graphics pipelines and interchange, this addon is meant to add first class support for USD Hydra rendering system to Blender. This allows rendering in Blender via the USD Hydra Framework.

## Additional Documentation
- [Pixar USD](https://graphics.pixar.com/usd/docs/index.html)
- [Hydra](https://graphics.pixar.com/usd/docs/USD-Glossary.html#USDGlossary-Hydra)
- [MaterialX](http://www.materialx.org/)

## Requirements
Currently, this addon works only with [Blender 4.0+](https://www.blender.org/download/) in Windows and Linux.

On the [releases](https://github.com/GPUOpen-LibrariesAndSDKs/BlenderUSDHydraAddon/releases) page are prebuilt versions of the ready to install addon. 

## Installing Add-on

Download the add-on from the releases page [releases](https://github.com/GPUOpen-LibrariesAndSDKs/BlenderUSDHydraAddon/releases). Open Blender preferences and got to the Add-ons section click Install button and pick the add-on in File Browser. Enable the add-on from the Add-ons section. 

>_WINDOWS USERS: Please note that old versions need to be disabled and uninstalled, and then Blender restarted. This is the case with many Blender addons that use C++ extensions: https://developer.blender.org/T77837_

## Usage
### Rendering
At a simple level, this functions similar to any render addon to Blender, like Cycles or EEVEE which are included in Blender. Simply select the render engine (in this case "Hydra RPR") and render using the `F12` key or starting a viewport render.

## Contributing
### Build Requirements
- Latest Blender precompiled libraries. Clone repository [Blender](https://projects.blender.org/blender/blender) and follow [instructions](https://wiki.blender.org/wiki/Building_Blender#:~:text=for%20Developers.-,Library%20Dependencies,-Details%20on%20obtaining) 
- [Python 3.10 x64](https://www.python.org/ftp/python/3.10.11/python-3.10.11.exe) _(Blender 4.0+ uses 3.10)_
  - requirements.txt

- [Visual Studio 2019 Community](https://my.visualstudio.com/Downloads?q=visual%20studio%202017&wt.mc_id=o~msft~vscom~older-downloads) _(Windows only)_
- [CMake 3.22.2+](https://cmake.org/download/). Make sure it's added to the PATH environment variable
- Subversion client, such as [TortoiseSVN](https://tortoisesvn.net/downloads.html)
- [Git for Windows](https://gitforwindows.org/)

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
- `deps/MaterialX` https://github.com/AcademySoftwareFoundation/MaterialX
- `deps/RadeonProRenderUSD` https://github.com/GPUOpen-LibrariesAndSDKs/RadeonProRenderUSD
- `deps/USD` https://github.com/PixarAnimationStudios/OpenUSD

All of them are included via SSH protocol. You will need to create and install [SSH keys](https://help.github.com/en/github/authenticating-to-github/connecting-to-github-with-ssh).

Once SSH keys are installed update/checkout submodules for active branch:
```commandline
> git submodule update --init -f --recursive
```

### Build
Require `python 3.10+` to be set by default.

#### Windows:
Use Open x64 Native Tools Command Prompt for Visual Studio 2019 Community and run.
```commandline
> git clone https://github.com/GPUOpen-LibrariesAndSDKs/BlenderUSDHydraAddon
> cd BlenderUSDHydraAddon
> git submodule update --init --recursive
> python build.py -all -bl-libs-dir <libs_dir> -bin-dir bin -addon
```

#### Linux:
```commandline
> git clone https://github.com/GPUOpen-LibrariesAndSDKs/BlenderUSDHydraAddon
> cd BlenderUSDHydraAddon
> git submodule update --init --recursive
> python tools/build.py -all -bl-libs-dir <libs_dir> -bin-dir bin -addon
```

For building on non-default system python version you should change it with `update-alternatives --config python` command or via setting venv.

#### Build tool
You can build project using `build.py` with different flag combinations. It allows you to create a folder with binaries and pack all the necessary files for development to `/install` folder. Also `build.py` provides a variety of ways to make a project builds:
- `-all` - builds all binaries, equals to `-usd -hdrpr -materialx -addon` 
- `-usd` - builds usd binaries
- `-hdrpr` - builds HdRPR plugin binaries
- `-materialx` - builds MaterialX binaries
- `-bin-dir <bin dir>` - define path to build binaries
- `-bl-libs-dir <libs_dir>` - define path to Blender precompiled libraries
- `-clean` - removes binaries folder before build, for example: `-all -clean ...` remove all folders in `<bin dir>`, `-usd -hdrpr -clean` removes only `<bin dir>/Usd` and `<bin dir>/HdRPR`
- `-G "Visual Studio 16 2019"` - set builder, passing with `-all` and `-hdrpr` _(Windows only)_ 
- `-addon` - generates zip archive with plugin to `/install` folder

Arguments are mostly used to skip build unneeded binaries. For example, you want switch to prebuild binary folder `bin/dir_01`:
```commandline
> python build.py -addon -hdrpr -bin-dir bin/dir_01
```
### Debugging
#### Visual Studio 2019
Recommended software for debugging, has really nice mixed python and C stack debugging. Provides to you ability of interactive code evaluation. You can make breakpoints move step by step, watch variables and etc.

##### 1. Run Blender with the Add-on
Make sure you have no installed addon for Blender version you want to use; remove installed version if needed.

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
