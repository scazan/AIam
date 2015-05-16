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

  const nite::Array<nite::UserData>& userDatas = userTrackerFrame.getUsers();
  for(int i = 0; i < userDatas.getSize(); ++i) {
    const nite::UserData& userData = userDatas[i];
    users[userData.getId()].updateState(userData, userTrackerFrame.getTimestamp());
    if(userData.isNew()) {
      userTracker->startSkeletonTracking(userData.getId());
    }
    else if(!userData.isLost()) {
      if(userData.getSkeleton().getState() == nite::SKELETON_TRACKED) {
	// send skeleton data here
      }
    }
  }
}

Tracker::User::User() {
  visible = false;
  skeletonState = nite::SKELETON_NONE;
}

void Tracker::User::updateState(const nite::UserData& userData, uint64_t ts) {
  if(userData.isNew()) {
    id = userData.getId();
    debug("New", ts);
  }

  else if(userData.isVisible() && !visible)
    printf("[%08" PRIu64 "] User #%d:\tVisible\n", ts, id);
  else if(!userData.isVisible() && visible)
    printf("[%08" PRIu64 "] User #%d:\tOut of Scene\n", ts, id);
  else if(userData.isLost()) {
    debug("Lost", ts);
  }
  visible = userData.isVisible();

  if(skeletonState != userData.getSkeleton().getState())
    {
      switch(skeletonState = userData.getSkeleton().getState())
	{
	case nite::SKELETON_NONE:
	  debug("Stopped tracking.", ts);
	  break;
	case nite::SKELETON_CALIBRATING:
	  debug("Calibrating...", ts);
	  break;
	case nite::SKELETON_TRACKED:
	  debug("Tracking!", ts);
	  break;
	case nite::SKELETON_CALIBRATION_ERROR_NOT_IN_POSE:
	case nite::SKELETON_CALIBRATION_ERROR_HANDS:
	case nite::SKELETON_CALIBRATION_ERROR_LEGS:
	case nite::SKELETON_CALIBRATION_ERROR_HEAD:
	case nite::SKELETON_CALIBRATION_ERROR_TORSO:
	  debug("Calibration Failed... :-|", ts);
	  break;
	}
    }
}

void Tracker::User::debug(const char *message, uint64_t ts) {
  printf("[%08" PRIu64 "] User #%d:\t%s\n", ts, id, message);
}
