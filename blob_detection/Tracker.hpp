#ifndef _TRACKER_HPP_
#define _TRACKER_HPP_

#include "Viewer.hpp"
#include <map>

class Tracker;

class TrackerViewer : public Viewer {
public:
  TrackerViewer(Tracker *);
  void processFrame();
  openni::VideoFrameRef getDepthFrame();

private:
  Tracker *tracker;
};

class Tracker {
public:
  Tracker();
  virtual ~Tracker();

  virtual openni::Status init(int argc, char **argv);
  virtual openni::Status mainLoop();

  openni::VideoFrameRef getDepthFrame();
  void processFrame();

private:
  openni::Device device;
  openni::VideoStream depthStream;
  openni::VideoFrameRef depthFrame;
  bool viewerEnabled;
  TrackerViewer *viewer;
  bool depthAsPoints;
};


#endif // _TRACKER_HPP_
