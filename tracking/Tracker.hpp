#ifndef _TRACKER_HPP_
#define _TRACKER_HPP_

#include "NiTE.h"

#define MAX_DEPTH 10000

class Tracker
{
public:
  Tracker();
  virtual ~Tracker();

  virtual openni::Status init();
  virtual openni::Status mainLoop();

private:
  Tracker(const Tracker&);
  Tracker& operator=(Tracker&);
  void processFrame();

  openni::Device m_device;
  nite::UserTracker* m_pUserTracker;
};


#endif // _TRACKER_HPP_
