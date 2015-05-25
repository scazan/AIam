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

  printf("User tracking initialized\n");

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
    else if(userData.isLost()) {
      printf("Lost %d\n", userData.getId());
    }
    else {
      if(userData.getSkeleton().getState() == nite::SKELETON_TRACKED) {
	sendSkeletonData(userData);
      }
      printStateIfChanged(userData);
    }
  }
}

void Tracker::printStateIfChanged(const nite::UserData& userData) {
  bool stateChanged = false;
  nite::SkeletonState newState = userData.getSkeleton().getState();
  if(previousStates.find(userData.getId()) == previousStates.end()) {
    stateChanged = true;
  }
  else if(newState != previousStates[userData.getId()]) {
    stateChanged = true;
  }
  if(stateChanged) {
    previousStates[userData.getId()] = newState;
    switch(newState) {
    case nite::SKELETON_NONE:
      printf("Stopped tracking %d\n", userData.getId());
      break;
    case nite::SKELETON_CALIBRATING:
      printf("Calibrating %d\n", userData.getId());
      break;
    case nite::SKELETON_TRACKED:
      printf("Tracking %d\n", userData.getId());
      break;
    case nite::SKELETON_CALIBRATION_ERROR_NOT_IN_POSE:
    case nite::SKELETON_CALIBRATION_ERROR_HANDS:
    case nite::SKELETON_CALIBRATION_ERROR_LEGS:
    case nite::SKELETON_CALIBRATION_ERROR_HEAD:
    case nite::SKELETON_CALIBRATION_ERROR_TORSO:
      printf("Calibration failed for %d\n", userData.getId());
      break;
    }
  }
}

void Tracker::sendSkeletonData(const nite::UserData& userData) {
  const nite::Skeleton skeleton = userData.getSkeleton();
  const nite::UserId userId = userData.getId();

  osc::OutboundPacketStream stream(oscBuffer, OSC_BUFFER_SIZE);
    
  stream << osc::BeginBundleImmediate;
  addJointData(stream, userId, skeleton, nite::JOINT_LEFT_HAND, "left_hand");
  addJointData(stream, userId, skeleton, nite::JOINT_RIGHT_HAND, "right_hand");
  addJointData(stream, userId, skeleton, nite::JOINT_HEAD, "head");
  addJointData(stream, userId, skeleton, nite::JOINT_NECK, "neck");
  addJointData(stream, userId, skeleton, nite::JOINT_LEFT_SHOULDER, "left_shoulder");
  addJointData(stream, userId, skeleton, nite::JOINT_LEFT_ELBOW, "left_elbow");
  addJointData(stream, userId, skeleton, nite::JOINT_RIGHT_SHOULDER, "right_shoulder");
  addJointData(stream, userId, skeleton, nite::JOINT_RIGHT_ELBOW, "right_elbow");
  addJointData(stream, userId, skeleton, nite::JOINT_TORSO, "torso");
  addJointData(stream, userId, skeleton, nite::JOINT_LEFT_HIP, "left_hip");
  addJointData(stream, userId, skeleton, nite::JOINT_LEFT_KNEE, "left_knee");
  addJointData(stream, userId, skeleton, nite::JOINT_RIGHT_HIP, "right_hip");
  addJointData(stream, userId, skeleton, nite::JOINT_RIGHT_KNEE, "right_knee");
  addJointData(stream, userId, skeleton, nite::JOINT_LEFT_FOOT, "left_foot");
  addJointData(stream, userId, skeleton, nite::JOINT_RIGHT_FOOT, "right_foot");
  stream << osc::EndBundle;
    
  transmitSocket->Send(stream.Data(), stream.Size());
}

void Tracker::addJointData(osc::OutboundPacketStream &stream,
			   const nite::UserId& userId,
			   const nite::Skeleton& skeleton,
			   nite::JointType type,
			   const char *jointName) {
  const nite::SkeletonJoint& joint = skeleton.getJoint(type);
  stream << osc::BeginMessage("/joint")
	 << userId
	 << jointName
	 << joint.getPosition().x
	 << joint.getPosition().y
	 << joint.getPosition().z
	 << osc::EndMessage;
}
