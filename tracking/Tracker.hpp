#ifndef _TRACKER_HPP_
#define _TRACKER_HPP_

#include "NiTE.h"

class Tracker
{
public:
  Tracker();
  virtual ~Tracker();

  virtual openni::Status init();
  virtual openni::Status mainLoop();

private:
  void processFrame();

  openni::Device device;
  nite::UserTracker* userTracker;
};


#endif // _TRACKER_HPP_
