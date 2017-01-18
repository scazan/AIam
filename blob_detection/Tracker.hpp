#ifndef _TRACKER_HPP_
#define _TRACKER_HPP_

#include "OpenNI.h"
#include <opencv2/video/tracking.hpp>
#include <opencv2/imgproc/imgproc.hpp>

#define MAX_DEPTH 10000

using namespace cv;

class Tracker {
public:
  Tracker();
  ~Tracker();

  openni::Status init(int argc, char **argv);
  void mainLoop();

private:
  openni::VideoFrameRef getDepthFrame();
  void processOpticalFlow();
  void Display();
  void ResizedWindow(int width, int height);
  void OnKey(unsigned char key, int x, int y);
  openni::Status InitOpenGL(int argc, char **argv);
  void InitOpenGLHooks();
  static void glutIdle();
  static void glutReshape(int width, int height);
  static void glutDisplay();
  static void glutKeyboard(unsigned char key, int x, int y);
  void updateTextureMap();
  void drawTextureMap();
  void drawTextureMapAsTexture();
  void drawTextureMapAsPoints();
  void drawOpticalFlow();

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
  int depthThreshold;

  Mat cvFrame, cvPreviousFrame;
  bool needToInit;
  vector<Point2f> points[2];
  vector<uchar> status;
};


#endif // _TRACKER_HPP_
