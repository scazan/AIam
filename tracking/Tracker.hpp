#ifndef _TRACKER_HPP_
#define _TRACKER_HPP_

#include "Viewer.hpp"
#include "NiTE.h"
#include <map>
#include <oscpack/osc/OscOutboundPacketStream.h>
#include <oscpack/ip/UdpSocket.h>

#define OSC_HOST "127.0.0.1"
#define OSC_PORT 15002
#define OSC_BUFFER_SIZE 1024

class Tracker;

class TrackerViewer : public Viewer {
public:
  TrackerViewer(Tracker *);
  void processFrame();
  nite::UserTracker *getUserTracker();
  nite::UserTrackerFrameRef getUserTrackerFrame();

private:
  Tracker *tracker;
};

class Tracker {
public:
  Tracker();
  virtual ~Tracker();

  virtual openni::Status init(int argc, char **argv);
  virtual openni::Status mainLoop();

  void processFrame();
  nite::UserTracker *getUserTracker() { return userTracker; }
  nite::UserTrackerFrameRef getUserTrackerFrame() { return userTrackerFrame; }

private:
  void sendBeginSession();
  void sendBeginFrame();
  void sendStatesAndSkeletonData();
  void sendSkeletonData(const nite::UserData&);
  void addJointData(osc::OutboundPacketStream &stream,
		    const nite::UserId& userId,
		    const nite::Skeleton& skeleton,
		    nite::JointType type,
		    const char *jointName);
  void sendStateIfChanged(const nite::UserData&);
  void sendState(const nite::UserId& userId, const char *state);
  void setSpeed();
  void stopSeeking();
  void disableFastForward();
  void enableFastForward();
  bool isCalibratingOrTracking();
  float getTimestamp();

  openni::Device device;
  openni::Recorder recorder;
  openni::VideoStream depthStream;
  nite::UserTracker* userTracker;
  nite::UserTrackerFrameRef userTrackerFrame;
  std::map<nite::UserId, nite::SkeletonState> previousStates;
  UdpTransmitSocket* transmitSocket;
  char oscBuffer[OSC_BUFFER_SIZE];
  bool seekingInRecording;
  bool fastForwarding;
  bool skipEmptySegments;
  int startFrameIndex;
  bool viewerEnabled;
  TrackerViewer *viewer;
  bool depthAsPoints;
};


#endif // _TRACKER_HPP_
