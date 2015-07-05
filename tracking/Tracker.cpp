#if (defined _WIN32)
#define PRIu64 "llu"
#else
#define __STDC_FORMAT_MACROS
#include <inttypes.h>
#endif

#include "Tracker.hpp"

#define FPS 30

Tracker::Tracker() {
  userTracker = new nite::UserTracker;
}

Tracker::~Tracker() {
  delete userTracker;
  nite::NiTE::shutdown();
  openni::OpenNI::shutdown();
}

openni::Status Tracker::init(int argc, char **argv) {
  const char *recordingFilename = NULL;
  float startTimeSecs = 0;
  bool overrideSmoothingFactor = false;
  float smoothingFactor = 0;

  openni::Status status = openni::OpenNI::initialize();
  if(status != openni::STATUS_OK) {
    printf("Failed to initialize OpenNI\n%s\n", openni::OpenNI::getExtendedError());
    return status;
  }

  const char* deviceUri = openni::ANY_DEVICE;
  for (int i = 1; i < argc-1; ++i) {
    if (strcmp(argv[i], "-device") == 0) {
      deviceUri = argv[++i];
    }

    else if(strcmp(argv[i], "-record") == 0) {
      recordingFilename = argv[++i];
    }

    else if(strcmp(argv[i], "-start") == 0) {
      startTimeSecs = atof(argv[++i]);
    }

    else if(strcmp(argv[i], "-smooth") == 0) {
      overrideSmoothingFactor = true;
      smoothingFactor = atof(argv[++i]);
    }

    else {
      printf("failed to parse argument: %s\n", argv[i]);
      return openni::STATUS_ERROR;
    }
  }

  status = device.open(deviceUri);
  if(status != openni::STATUS_OK) {
    printf("Failed to open device\n%s\n", openni::OpenNI::getExtendedError());
    return status;
  }

  status = depthStream.create(device, openni::SENSOR_DEPTH);
  if (status == openni::STATUS_OK) {
    openni::VideoMode depthMode = depthStream.getVideoMode();
    depthMode.setFps(FPS);
    depthMode.setResolution(640, 480);
    depthMode.setPixelFormat(openni::PIXEL_FORMAT_DEPTH_1_MM);
    status = depthStream.setVideoMode(depthMode); 
    if(status == openni::STATUS_OK){
      status = depthStream.start();
      if (status != openni::STATUS_OK) {
	printf("Couldn't start depth stream:\n%s\n", openni::OpenNI::getExtendedError());
	depthStream.destroy();
      }
    }
  }
  else {
    printf("Couldn't find depth stream:\n%s\n", openni::OpenNI::getExtendedError());
  }

  if(recordingFilename != NULL) {
    if(access(recordingFilename, F_OK) == 0) {
      printf("file '%s' already exists\n", recordingFilename);
      return openni::STATUS_ERROR;
    }

    recorder.create(recordingFilename);
    recorder.attach(depthStream);
    recorder.start();
  }

  nite::NiTE::initialize();

  if(userTracker->create(&device) != nite::STATUS_OK) {
    return openni::STATUS_ERROR;
  }

  if(overrideSmoothingFactor) {
    float defaultSmoothingFactor = userTracker->getSkeletonSmoothingFactor();
    if(userTracker->setSkeletonSmoothingFactor(smoothingFactor) == nite::STATUS_OK)
      printf("Skeleton smoothing factor was set to %f (default is %f)\n",
	     smoothingFactor, defaultSmoothingFactor);
    else
      printf("Failed to set smoothing factor to %f (default is %f)\n",
	     smoothingFactor, defaultSmoothingFactor);
  }

  if(startTimeSecs > 0) {
    startFrameIndex = (int) (startTimeSecs * FPS);
    printf("Total number of frames: %d\n", device.getPlaybackControl()->getNumberOfFrames(depthStream));
    printf("Fast-forwarding to frame %d\n", startFrameIndex);
    seekingInRecording = true;
    fastForwarding = false;
  }
  else {
    seekingInRecording = false;
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
  if(seekingInRecording)
    setSpeed();

  openni::VideoFrameRef depthFrame;
  nite::Status status = userTracker->readFrame(&userTrackerFrame);
  if(status != nite::STATUS_OK) {
    printf("GetNextData failed\n");
    return;
  }

  sendBeginFrame();
  sendStatesAndSkeletonData();
}

void Tracker::setSpeed() {
  if(seekingInRecording) {
    bool calibrating = isCalibrating();
    if(fastForwarding) {
      if(userTrackerFrame.getFrameIndex() >= startFrameIndex)
	stopSeeking();
      else if(calibrating)
	disableFastForward();
    }
    else if(!fastForwarding && !calibrating)
      enableFastForward();
  }
}

bool Tracker::isCalibrating() {
  const nite::Array<nite::UserData>& users = userTrackerFrame.getUsers();
  for(int i = 0; i < users.getSize(); ++i) {
    const nite::UserData& userData = users[i];
    nite::SkeletonState state = userData.getSkeleton().getState();
    if(state == nite::SKELETON_CALIBRATING)
      return true;
  }
  return false;
}

void Tracker::stopSeeking() {
  printf("Stopping fast-forward after having reached frame %d\n", userTrackerFrame.getFrameIndex());
  disableFastForward();
  seekingInRecording = false;
}

void Tracker::disableFastForward() {
  printf("resuming normal speed\n");
  openni::Status status = device.getPlaybackControl()->setSpeed(1.0);
  if(status != openni::STATUS_OK)
    printf("setSpeed failed\n");
  fastForwarding = false;
}

void Tracker::enableFastForward() {
  printf("fast-forwarding\n");
  openni::Status status = device.getPlaybackControl()->setSpeed(100.0);
  if(status != openni::STATUS_OK)
    printf("setSpeed failed\n");
  fastForwarding = true;
}

void Tracker::sendBeginFrame() {
  osc::OutboundPacketStream stream(oscBuffer, OSC_BUFFER_SIZE);
  float timestampMilliSeconds = (float) userTrackerFrame.getTimestamp() / 1000;
  stream << osc::BeginBundleImmediate
	 << osc::BeginMessage("/begin_frame") << timestampMilliSeconds
	 << osc::EndMessage
	 << osc::EndBundle;
  transmitSocket->Send(stream.Data(), stream.Size());
}

void Tracker::sendStatesAndSkeletonData() {
  const nite::Array<nite::UserData>& users = userTrackerFrame.getUsers();
  for(int i = 0; i < users.getSize(); ++i) {
    const nite::UserData& userData = users[i];
    if(userData.isNew()) {
      sendState(userData.getId(), "new");
      userTracker->startSkeletonTracking(userData.getId());
    }
    else if(userData.isLost()) {
      sendState(userData.getId(), "lost");
    }
    else {
      if(userData.getSkeleton().getState() == nite::SKELETON_TRACKED) {
	sendSkeletonData(userData);
      }
      sendStateIfChanged(userData);
    }
  }
}

void Tracker::sendStateIfChanged(const nite::UserData& userData) {
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
      sendState(userData.getId(), "stopped_tracking");
      break;
    case nite::SKELETON_CALIBRATING:
      sendState(userData.getId(), "calibrating");
      break;
    case nite::SKELETON_TRACKED:
      sendState(userData.getId(), "tracking");
      break;
    case nite::SKELETON_CALIBRATION_ERROR_NOT_IN_POSE:
    case nite::SKELETON_CALIBRATION_ERROR_HANDS:
    case nite::SKELETON_CALIBRATION_ERROR_LEGS:
    case nite::SKELETON_CALIBRATION_ERROR_HEAD:
    case nite::SKELETON_CALIBRATION_ERROR_TORSO:
      sendState(userData.getId(), "calibration_failed");
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
	 << joint.getPositionConfidence()
	 << osc::EndMessage;
}

void Tracker::sendState(const nite::UserId& userId, const char *state) {
  printf("%s %d\n", state, userId);
  osc::OutboundPacketStream stream(oscBuffer, OSC_BUFFER_SIZE);
  stream << osc::BeginBundleImmediate
	 << osc::BeginMessage("/state") << userId << state
	 << osc::EndMessage
	 << osc::EndBundle;
  transmitSocket->Send(stream.Data(), stream.Size());
}
