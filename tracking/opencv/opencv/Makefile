all: lkdemo blob_detection

lkdemo.o: lkdemo.cpp
	g++ -c -O2 -Wall -o lkdemo.o lkdemo.cpp

lkdemo: lkdemo.o
	g++ -o lkdemo lkdemo.o -lopencv_core -lopencv_imgproc -lopencv_video -lopencv_highgui

blob_detection.o: blob_detection.cpp
	g++ -c -O2 -Wall -o blob_detection.o blob_detection.cpp

blob_detection: blob_detection.o
	g++ -o blob_detection blob_detection.o -lopencv_core -lopencv_features2d -lopencv_highgui
