ALLOW_WARNINGS = 1
include CommonDefs.mak

OSCPACK = libs

ifeq ("$(OSTYPE)","Darwin")
	NITE2_INCLUDE = libs/openni2/include
	OPENNI2_INCLUDE = libs/openni2/include
endif

BIN_DIR = Bin

INC_DIRS = \
	${NITE2_INCLUDE} \
	$(OPENNI2_INCLUDE) \
	$(OSCPACK)

SRC_FILES = *.cpp

ifeq ("$(OSTYPE)","Darwin")
	CFLAGS += -DMACOS
	LDFLAGS += -framework OpenGL -framework GLUT -Llibs/openni2/lib/macosx/ -Llibs/oscpack
else
	CFLAGS += -DUNIX
	USED_LIBS += glut GL GLU
endif

LIB_DIRS += $(OPENNI2_REDIST) $(NITE2_REDIST) $(NITE2_REDIST64)

USED_LIBS += OpenNI2 NiTE2 oscpack

EXE_NAME = Tracker

CFLAGS += -Wall

include CommonCppMakefile
