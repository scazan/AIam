ALLOW_WARNINGS = 1
include CommonDefs.mak

ifeq ("$(OSTYPE)","Darwin")
	OPENNI2_INCLUDE = libs/openni2/include
endif

BIN_DIR = Bin

INC_DIRS = \
	$(OPENNI2_INCLUDE)

SRC_FILES = *.cpp

ifeq ("$(OSTYPE)","Darwin")
	CFLAGS += -DMACOS
	LDFLAGS += -framework OpenGL -framework GLUT -Llibs/openni2/lib/macosx/
else
	CFLAGS += -DUNIX
	USED_LIBS += glut GL GLU
endif

LIB_DIRS += $(OPENNI2_REDIST)

USED_LIBS += OpenNI2

EXE_NAME = Tracker

CFLAGS += -Wall

include CommonCppMakefile
