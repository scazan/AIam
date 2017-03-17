#ifndef _TRACKER_HPP_
#define _TRACKER_HPP_

#include "OpenNI.h"
#include <opencv2/imgproc/imgproc.hpp>
#include "TextureRenderer.hpp"

#define MAX_DEPTH 10000

using namespace cv;

class Tracker;

class ProcessingMethod {
public:
  ProcessingMethod(Tracker *tracker);
  virtual ~ProcessingMethod() {}
  virtual void processDepthFrame(Mat&)=0;
  virtual void render()=0;
  virtual void onKey(unsigned char key)=0;

protected:
  int width, height;
  Tracker *tracker;
};

class WorldRange {
public:
  float xMin;
  float xMax;
  float yMin;
  float yMax;
};

class Tracker {
public:
  Tracker();
  ~Tracker();
  openni::Status init(int argc, char **argv);
  void mainLoop();
  int getResolutionX() { return resolutionX; }
  int getResolutionY() { return resolutionY; }
  const WorldRange& getWorldRange() { return worldRange; }
  TextureRenderer* getTextureRenderer() { return textureRenderer; }
  bool depthAsPoints;

private:
  void processOniDepthFrame();
  void display();
  void onWindowResized(int width, int height);
  void onKey(unsigned char key);
  openni::Status initOpenGL(int argc, char **argv);
  void initOpenGLHooks();
  static void glutIdle();
  static void glutReshape(int width, int height);
  static void glutDisplay();
  static void glutKeyboard(unsigned char key, int x, int y);
  void drawDepthFrame();
  void calculateWorldRange();
  void setSpeed();
  void stopSeeking();
  void disableFastForward();
  void enableFastForward();

  static Tracker* self;
  openni::Device device;
  openni::Recorder recorder;
  openni::VideoStream depthStream;
  openni::VideoFrameRef oniDepthFrame;
  Mat depthFrame;
  Mat zThresholdedDepthFrame;
  int oniWidth, oniHeight;
  int resolutionX, resolutionY;
  TextureRenderer *textureRenderer;
  uint64_t previousDisplayTime;
  int windowWidth, windowHeight;
  int zThreshold;
  bool processingEnabled;
  ProcessingMethod *processingMethod;
  WorldRange worldRange;
  bool displayDepth;
  bool displayZThresholding;
  bool paused;
  bool seekingInRecording;
  bool fastForwarding;
  int startFrameIndex;
};


#endif // _TRACKER_HPP_
