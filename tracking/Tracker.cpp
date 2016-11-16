#if (defined _WIN32)
#define PRIu64 "llu"
#else
#define __STDC_FORMAT_MACROS
#include <inttypes.h>
#endif

#include "Tracker.hpp"

extern bool verbose;

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
  int fps = 30;
  skipEmptySegments = false;
  fastForwarding = false;
  viewerEnabled = false;
  depthAsPoints = false;

  openni::Status status = openni::OpenNI::initialize();
  if(status != openni::STATUS_OK) {
    printf("Failed to initialize OpenNI\n%s\n", openni::OpenNI::getExtendedError());
    return status;
  }

  const char* deviceUri = openni::ANY_DEVICE;
  const char* oscHost = DEFAULT_OSC_HOST;
  for (int i = 1; i < argc; ++i) {
    if (strcmp(argv[i], "-device") == 0) {
      deviceUri = argv[++i];
    }

    else if(strcmp(argv[i], "-record") == 0) {
      recordingFilename = argv[++i];
    }

    else if(strcmp(argv[i], "-start") == 0) {
      startTimeSecs = atof(argv[++i]);
    }

    else if(strcmp(argv[i], "-skip") == 0) {
      skipEmptySegments = true;
    }

    else if(strcmp(argv[i], "-smooth") == 0) {
      overrideSmoothingFactor = true;
      smoothingFactor = atof(argv[++i]);
    }

    else if(strcmp(argv[i], "-with-viewer") == 0) {
      viewerEnabled = true;
    }

    else if(strcmp(argv[i], "-verbose") == 0) {
      verbose = true;
    }

    else if(strcmp(argv[i], "-depth-as-points") == 0) {
      depthAsPoints = true;
    }

    else if(strcmp(argv[i], "-fps") == 0) {
      fps = atoi(argv[++i]);
    }

    else if(strcmp(argv[i], "-osc-host") == 0) {
      oscHost = argv[++i];
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
    depthMode.setFps(fps);
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
    startFrameIndex = (int) (startTimeSecs * fps);
    printf("Total number of frames: %d\n", device.getPlaybackControl()->getNumberOfFrames(depthStream));
    printf("Fast-forwarding to frame %d\n", startFrameIndex);
    seekingInRecording = true;
  }
  else {
    seekingInRecording = false;
  }

  transmitSocket = new UdpTransmitSocket(IpEndpointName(oscHost, OSC_PORT));

  printf("User tracking initialized\n");
  sendBeginSession();

  if(viewerEnabled) {
    viewer = new TrackerViewer(this);
    viewer->depthAsPoints = depthAsPoints;
    viewer->Init(argc, argv);
  }

  return openni::STATUS_OK;
}

openni::Status Tracker::mainLoop() {
  if(viewerEnabled) {
    viewer->Run();
  }
  else {
    while(true) {
      processFrame();
    }
  }
  return openni::STATUS_OK;
}

void Tracker::processFrame() {
  setSpeed();

  nite::Status status = userTracker->readFrame(&userTrackerFrame);
  if(status != nite::STATUS_OK) {
    printf("GetNextData failed\n");
    return;
  }

  sendBeginFrame();
  sendStatesAndSkeletonData();
  sendCenterOfMass();
}

void Tracker::setSpeed() {
  if(seekingInRecording) {
    if(fastForwarding && userTrackerFrame.getFrameIndex() >= startFrameIndex)
      stopSeeking();
    else if(!fastForwarding)
      enableFastForward();
  }
  else if(skipEmptySegments) {
    bool calibratingOrTracking = isCalibratingOrTracking();
    if(fastForwarding && calibratingOrTracking)
      disableFastForward();
    else if(!fastForwarding && !calibratingOrTracking)
      enableFastForward();
  }
}

bool Tracker::isCalibratingOrTracking() {
  const nite::Array<nite::UserData>& users = userTrackerFrame.getUsers();
  for(int i = 0; i < users.getSize(); ++i) {
    const nite::UserData& userData = users[i];
    nite::SkeletonState state = userData.getSkeleton().getState();
    if(state == nite::SKELETON_CALIBRATING || state == nite::SKELETON_TRACKED)
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

void Tracker::sendBeginSession() {
  osc::OutboundPacketStream stream(oscBuffer, OSC_BUFFER_SIZE);
  stream << osc::BeginBundleImmediate
	 << osc::BeginMessage("/begin_session")
	 << osc::EndMessage
	 << osc::EndBundle;
  transmitSocket->Send(stream.Data(), stream.Size());
}

void Tracker::sendBeginFrame() {
  osc::OutboundPacketStream stream(oscBuffer, OSC_BUFFER_SIZE);
  stream << osc::BeginBundleImmediate
	 << osc::BeginMessage("/begin_frame") << getTimestamp()
	 << osc::EndMessage
	 << osc::EndBundle;
  transmitSocket->Send(stream.Data(), stream.Size());
}

float Tracker::getTimestamp() {
  float timestampMilliSeconds = (float) userTrackerFrame.getTimestamp() / 1000;
  return timestampMilliSeconds;
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
	 << joint.getOrientation().w
	 << joint.getOrientation().x
	 << joint.getOrientation().y
	 << joint.getOrientation().z
	 << joint.getOrientationConfidence()
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

void Tracker::sendCenterOfMass() {
  const nite::Array<nite::UserData>& users = userTrackerFrame.getUsers();
  for (int i = 0; i < users.getSize(); ++i) {
    const nite::UserData& user = users[i];
    const nite::Point3f& center = user.getCenterOfMass();
    osc::OutboundPacketStream stream(oscBuffer, OSC_BUFFER_SIZE);
    stream << osc::BeginBundleImmediate
	   << osc::BeginMessage("/center") << user.getId() << center.x << center.y << center.z
	   << osc::EndMessage
	   << osc::EndBundle;
    transmitSocket->Send(stream.Data(), stream.Size());
  }
}

TrackerViewer::TrackerViewer(Tracker *_tracker) : Viewer() {
  tracker = _tracker;
}

void TrackerViewer::processFrame() {
  tracker->processFrame();
}

nite::UserTracker *TrackerViewer::getUserTracker() {
  return tracker->getUserTracker();
}

nite::UserTrackerFrameRef TrackerViewer::getUserTrackerFrame() {
  return tracker->getUserTrackerFrame();
}
