lkdemo.o: lkdemo.cpp
	g++ -c -O2 -Wall -o lkdemo.o lkdemo.cpp

lkdemo: lkdemo.o
	g++ -o lkdemo lkdemo.o -lopencv_core -lopencv_imgproc -lopencv_video -lopencv_highgui
