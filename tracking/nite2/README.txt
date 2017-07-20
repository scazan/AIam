INSTALLING ON OSX

download Openni2 binaries
https://app.box.com/s/msh82mkq8wd7b17pxv33czi0b51ia9l9

and includes
https://github.com/gaborpapp/Cinder-NI-nolibs

and place them in lib/openni2

build lib/oscpack by typing 'make lib'

type 'make' in tracker, which should build the binary in Bin/x64-Release

copy libs/oscpack/liboscpack.dylib and the contents of libs/openni2/lib/macosx
next to the Tracker executable.
