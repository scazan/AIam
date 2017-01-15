#if (defined _WIN32)
#define PRIu64 "llu"
#else
#define __STDC_FORMAT_MACROS
#include <inttypes.h>
#endif

#include "Tracker.hpp"

extern bool verbose;

Tracker::Tracker() {
}

Tracker::~Tracker() {
  openni::OpenNI::shutdown();
}

openni::Status Tracker::init(int argc, char **argv) {
  int fps = 30;
  viewerEnabled = false;
  depthAsPoints = false;

  openni::Status status = openni::OpenNI::initialize();
  if(status != openni::STATUS_OK) {
    printf("Failed to initialize OpenNI\n%s\n", openni::OpenNI::getExtendedError());
    return status;
  }

  const char* deviceUri = openni::ANY_DEVICE;
  for (int i = 1; i < argc; ++i) {
    if (strcmp(argv[i], "-device") == 0) {
      deviceUri = argv[++i];
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

openni::VideoFrameRef Tracker::getDepthFrame() {
  openni::Status status = depthStream.readFrame(&depthFrame);
  if (status != openni::STATUS_OK) {
    printf("Couldn't read depth frame:\n%s\n", openni::OpenNI::getExtendedError());
  }
  return depthFrame;
}

void Tracker::processFrame() {
}

TrackerViewer::TrackerViewer(Tracker *_tracker) : Viewer() {
  tracker = _tracker;
}

void TrackerViewer::processFrame() {
  tracker->processFrame();
}

openni::VideoFrameRef TrackerViewer::getDepthFrame() {
  return tracker->getDepthFrame();
}
