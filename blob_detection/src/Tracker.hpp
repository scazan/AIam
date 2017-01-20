#ifndef _TRACKER_HPP_
#define _TRACKER_HPP_

#include "OpenNI.h"

#define MAX_DEPTH 10000

class ProcessingMethod {
public:
  ProcessingMethod(int width, int height, int depthThreshold) {
    this->width = width;
    this->height = height;
    this->depthThreshold = depthThreshold;
  }
  virtual void processDepthFrame(openni::VideoFrameRef)=0;
  virtual void render()=0;
  virtual void onKey(unsigned char key)=0;

protected:
  int width, height;
  int depthThreshold;
};

class Tracker {
public:
  Tracker();
  ~Tracker();

  openni::Status init(int argc, char **argv);
  void mainLoop();

private:
  openni::VideoFrameRef getDepthFrame();
  void Display();
  void ResizedWindow(int width, int height);
  void onKey(unsigned char key);
  openni::Status InitOpenGL(int argc, char **argv);
  void InitOpenGLHooks();
  static void glutIdle();
  static void glutReshape(int width, int height);
  static void glutDisplay();
  static void glutKeyboard(unsigned char key, int x, int y);
  void calculateHistogram();
  void updateTextureMap();
  void drawTextureMap();
  void drawTextureMapAsTexture();
  void drawTextureMapAsPoints();

  static Tracker* self;
  openni::Device device;
  openni::VideoStream depthStream;
  openni::VideoFrameRef depthFrame;
  int width, height;
  bool depthAsPoints;
  openni::RGB888Pixel* textureMap;
  unsigned int textureMapWidth;
  unsigned int textureMapHeight;
  uint64_t previousDisplayTime;
  int windowWidth, windowHeight;
  int depthThreshold;
  float	histogram[MAX_DEPTH];
  float histogramEnabled;
  bool processingEnabled;
  ProcessingMethod *processingMethod;
};


#endif // _TRACKER_HPP_
