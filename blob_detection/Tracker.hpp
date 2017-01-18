#ifndef _TRACKER_HPP_
#define _TRACKER_HPP_

#include "OpenNI.h"

#define MAX_DEPTH 10000

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
  openni::Status InitOpenGL(int argc, char **argv);
  void InitOpenGLHooks();
  static void glutIdle();
  static void glutReshape(int width, int height);
  static void glutDisplay();
  void updateTextureMap();
  void drawTextureMap();
  void drawTextureMapAsTexture();
  void drawTextureMapAsPoints();

  static Tracker* self;
  openni::Device device;
  openni::VideoStream depthStream;
  openni::VideoFrameRef depthFrame;
  bool depthAsPoints;
  openni::RGB888Pixel* m_pTexMap;
  unsigned int m_nTexMapX;
  unsigned int m_nTexMapY;
  uint64_t previousDisplayTime;
  int windowWidth, windowHeight;
};


#endif // _TRACKER_HPP_
