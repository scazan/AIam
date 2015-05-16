include CommonDefs.mak

BIN_DIR = Bin

INC_DIRS = \
	${NITE2_INCLUDE} \
	$(OPENNI2_INCLUDE)

SRC_FILES = *.cpp

ifeq ("$(OSTYPE)","Darwin")
	CFLAGS += -DMACOS
else
	CFLAGS += -DUNIX
endif

LIB_DIRS += $(OPENNI2_REDIST) $(NITE2_REDIST)

USED_LIBS += OpenNI2 NiTE2

EXE_NAME = Tracker

CFLAGS += -Wall

include CommonCppMakefile
