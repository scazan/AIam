#ifndef _TRACKER_HPP_
#define _TRACKER_HPP_

#include "NiTE.h"
#include <map>
#include <oscpack/osc/OscOutboundPacketStream.h>
#include <oscpack/ip/UdpSocket.h>

#define OSC_HOST "127.0.0.1"
#define OSC_PORT 15002
#define OSC_BUFFER_SIZE 1024

class Tracker {
public:
  Tracker();
  virtual ~Tracker();

  virtual openni::Status init();
  virtual openni::Status mainLoop();

private:
  void processFrame();
  void sendSkeletonData(const nite::Skeleton&);
  void printStateIfChanged(const nite::UserData&);

  openni::Device device;
  nite::UserTracker* userTracker;
  std::map<nite::UserId, nite::SkeletonState> previousStates;
  UdpTransmitSocket* transmitSocket;
  char oscBuffer[OSC_BUFFER_SIZE];
};


#endif // _TRACKER_HPP_
