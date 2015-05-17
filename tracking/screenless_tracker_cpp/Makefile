include CommonDefs.mak

OSCPACK = /usr/local/include

BIN_DIR = Bin

INC_DIRS = \
	${NITE2_INCLUDE} \
	$(OPENNI2_INCLUDE) \
	$(OSCPACK)

SRC_FILES = *.cpp

ifeq ("$(OSTYPE)","Darwin")
	CFLAGS += -DMACOS
else
	CFLAGS += -DUNIX
endif

LIB_DIRS += $(OPENNI2_REDIST) $(NITE2_REDIST)

USED_LIBS += OpenNI2 NiTE2 oscpack

EXE_NAME = Tracker

CFLAGS += -Wall

include CommonCppMakefile
