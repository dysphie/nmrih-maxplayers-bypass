# MaxPlayers Patch

Lets you run 9-player servers again in No More Room in Hell.

I'll make this a proper MetaMod extension at some point, maybe.

# Drag-n-drop

* Download the patched binaries from [releases](https://github.com/dysphie/nmrih-maxplayers-bypass/) and replace the ones on your server.
* On Linux, you might need to `chmod +x` the file again. Google it.

# Or patch them yourself

* Install Python.
* Run `binpatch.py` on the binary, e.g. `python binpatch.py apply server.so`.
* Grab the `_patched` file, rename it, and upload it to your server.
