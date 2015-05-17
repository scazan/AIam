#if (defined _WIN32)
#define PRIu64 "llu"
#else
#define __STDC_FORMAT_MACROS
#include <inttypes.h>
#endif

#include "Tracker.hpp"

Tracker::Tracker() {
  userTracker = new nite::UserTracker;
}

Tracker::~Tracker() {
  delete userTracker;
  nite::NiTE::shutdown();
  openni::OpenNI::shutdown();
}

openni::Status Tracker::init() {
  openni::Status status = openni::OpenNI::initialize();
  if(status != openni::STATUS_OK) {
    printf("Failed to initialize OpenNI\n%s\n", openni::OpenNI::getExtendedError());
    return status;
  }

  const char* deviceUri = openni::ANY_DEVICE;
  status = device.open(deviceUri);
  if(status != openni::STATUS_OK) {
    printf("Failed to open device\n%s\n", openni::OpenNI::getExtendedError());
    return status;
  }

  nite::NiTE::initialize();

  if(userTracker->create(&device) != nite::STATUS_OK) {
    return openni::STATUS_ERROR;
  }

  transmitSocket = new UdpTransmitSocket(IpEndpointName(OSC_HOST, OSC_PORT));

  return openni::STATUS_OK;
}

openni::Status Tracker::mainLoop() {
  while(true) {
    processFrame();
  }
  return openni::STATUS_OK;
}

void Tracker::processFrame() {
  nite::UserTrackerFrameRef userTrackerFrame;
  openni::VideoFrameRef depthFrame;
  nite::Status status = userTracker->readFrame(&userTrackerFrame);
  if(status != nite::STATUS_OK) {
    printf("GetNextData failed\n");
    return;
  }

  const nite::Array<nite::UserData>& users = userTrackerFrame.getUsers();
  for(int i = 0; i < users.getSize(); ++i) {
    const nite::UserData& userData = users[i];
    if(userData.isNew()) {
      printf("New %d\n", userData.getId());
      userTracker->startSkeletonTracking(userData.getId());
    }
    if(!userData.isLost()) {
      printf("%d in state %d\n", userData.getId(), userData.getSkeleton().getState());
      if(userData.getSkeleton().getState() == nite::SKELETON_TRACKED) {
	sendSkeletonData(userData.getSkeleton());
      }
    }
  }
}

void Tracker::sendSkeletonData(const nite::Skeleton &skeleton) {
  const nite::SkeletonJoint& torso = skeleton.getJoint(nite::JOINT_TORSO);

  printf("%.3f %.3f %.3f\n",
	 torso.getPosition().x,
	 torso.getPosition().y,
	 torso.getPosition().z);

  osc::OutboundPacketStream p(oscBuffer, OSC_BUFFER_SIZE);
    
  p << osc::BeginBundleImmediate
    << osc::BeginMessage( "/test1" ) 
    << true << 23 << (float)3.1415 << "hello" << osc::EndMessage
    << osc::BeginMessage( "/test2" ) 
    << true << 24 << (float)10.8 << "world" << osc::EndMessage
    << osc::EndBundle;
    
  transmitSocket->Send(p.Data(), p.Size());
}
