#if (defined _WIN32)
#define PRIu64 "llu"
#else
#define __STDC_FORMAT_MACROS
#include <inttypes.h>
#endif

#include "Tracker.hpp"

#include "NiteSampleUtilities.h"

Tracker::Tracker() {
  m_pUserTracker = new nite::UserTracker;
}

Tracker::~Tracker() {
  delete m_pUserTracker;
  nite::NiTE::shutdown();
  openni::OpenNI::shutdown();
}

openni::Status Tracker::init() {
  openni::Status rc = openni::OpenNI::initialize();
  if (rc != openni::STATUS_OK) {
    printf("Failed to initialize OpenNI\n%s\n", openni::OpenNI::getExtendedError());
    return rc;
  }

  const char* deviceUri = openni::ANY_DEVICE;
  rc = m_device.open(deviceUri);
  if (rc != openni::STATUS_OK) {
      printf("Failed to open device\n%s\n", openni::OpenNI::getExtendedError());
      return rc;
    }

  nite::NiTE::initialize();

  if (m_pUserTracker->create(&m_device) != nite::STATUS_OK) {
    return openni::STATUS_ERROR;
  }

  return openni::STATUS_OK;
}

openni::Status Tracker::mainLoop() {
  while(true)
    processFrame();
  return openni::STATUS_OK;
}

#define MAX_USERS 10
bool g_visibleUsers[MAX_USERS] = {false};
nite::SkeletonState g_skeletonStates[MAX_USERS] = {nite::SKELETON_NONE};
char g_userStatusLabels[MAX_USERS][100] = {{0}};

char g_generalMessage[100] = {0};

#define USER_MESSAGE(msg) {\
	sprintf(g_userStatusLabels[user.getId()], "%s", msg);\
	printf("[%08" PRIu64 "] User #%d:\t%s\n", ts, user.getId(), msg);}

void updateUserState(const nite::UserData& user, uint64_t ts) {
  if (user.isNew())
    {
      USER_MESSAGE("New");
    }
  else if (user.isVisible() && !g_visibleUsers[user.getId()])
    printf("[%08" PRIu64 "] User #%d:\tVisible\n", ts, user.getId());
  else if (!user.isVisible() && g_visibleUsers[user.getId()])
    printf("[%08" PRIu64 "] User #%d:\tOut of Scene\n", ts, user.getId());
  else if (user.isLost())
    {
      USER_MESSAGE("Lost");
    }
  g_visibleUsers[user.getId()] = user.isVisible();

  if(g_skeletonStates[user.getId()] != user.getSkeleton().getState())
    {
      switch(g_skeletonStates[user.getId()] = user.getSkeleton().getState())
	{
	case nite::SKELETON_NONE:
	  USER_MESSAGE("Stopped tracking.")
	    break;
	case nite::SKELETON_CALIBRATING:
	  USER_MESSAGE("Calibrating...")
	    break;
	case nite::SKELETON_TRACKED:
	  USER_MESSAGE("Tracking!")
	    break;
	case nite::SKELETON_CALIBRATION_ERROR_NOT_IN_POSE:
	case nite::SKELETON_CALIBRATION_ERROR_HANDS:
	case nite::SKELETON_CALIBRATION_ERROR_LEGS:
	case nite::SKELETON_CALIBRATION_ERROR_HEAD:
	case nite::SKELETON_CALIBRATION_ERROR_TORSO:
	  USER_MESSAGE("Calibration Failed... :-|")
	    break;
	}
    }
}

void Tracker::processFrame() {
  nite::UserTrackerFrameRef userTrackerFrame;
  openni::VideoFrameRef depthFrame;
  nite::Status rc = m_pUserTracker->readFrame(&userTrackerFrame);
  if (rc != nite::STATUS_OK) {
    printf("GetNextData failed\n");
    return;
  }

  const nite::Array<nite::UserData>& users = userTrackerFrame.getUsers();
  for (int i = 0; i < users.getSize(); ++i) {
    const nite::UserData& user = users[i];
    updateUserState(user, userTrackerFrame.getTimestamp());
    if (user.isNew()) {
      m_pUserTracker->startSkeletonTracking(user.getId());
    }
    else if (!user.isLost()) {
      if (users[i].getSkeleton().getState() == nite::SKELETON_TRACKED) {
	// send skeleton data here
      }
    }
  }
}
