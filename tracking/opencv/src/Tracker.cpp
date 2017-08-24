#if (defined _WIN32)
#define PRIu64 "llu"
#else
#define __STDC_FORMAT_MACROS
#include <inttypes.h>
#endif

#include "Tracker.hpp"
#include "BlobTracker.hpp"
#include <sys/time.h>
#include <stdarg.h>

#if (ONI_PLATFORM == ONI_PLATFORM_MACOSX)
#include <GLUT/glut.h>
#else
#include <GL/glut.h>
#endif

#define GL_WIN_SIZE_X        640
#define GL_WIN_SIZE_Y        480

#define DEFAULT_DISPLAY_MODE        DISPLAY_MODE_DEPTH

bool verbose = false;
Tracker* Tracker::self = NULL;

void log(const char *format, ...) {
  va_list args;
  if(verbose) {
    va_start(args, format);
    vfprintf(stdout, format, args);
    va_end(args);
    fflush(stdout);
  }
}

#define checkGlErrors() _checkGlErrors(__LINE__)

int _checkGlErrors(int line) {
  GLenum err;
  int numErrors = 0;
  while ((err = glGetError()) != GL_NO_ERROR) {
    printf("OpenGL error at line %d: %s\n", line, gluErrorString(err));
    numErrors++;
  }
  return numErrors;
}
Tracker::Tracker() {
  self = this;
}

Tracker::~Tracker() {
  delete textureRenderer;
  openni::OpenNI::shutdown();
}

openni::Status Tracker::init(int argc, char **argv) {
  int fps = 30;
  resolutionX = resolutionY = 0;
  depthAsPoints = false;
  zThreshold = 0;
  minBlobArea = DEFAULT_MIN_BLOB_AREA;
  maxBlobArea = DEFAULT_MAX_BLOB_AREA;
  paused = false;
  bool listDevices = false;

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

    else if(strcmp(argv[i], "-list-devices") == 0) {
      listDevices = true;
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

    else if(strcmp(argv[i], "-zt") == 0) {
      zThreshold = atoi(argv[++i]);
    }

    else if(strcmp(argv[i], "-rx") == 0) {
      resolutionX = atoi(argv[++i]);
    }

    else if(strcmp(argv[i], "-ry") == 0) {
      resolutionY = atoi(argv[++i]);
    }

    else if(strcmp(argv[i], "-min-area") == 0) {
      minBlobArea = atof(argv[++i]);
    }

    else if(strcmp(argv[i], "-max-area") == 0) {
      maxBlobArea = atof(argv[++i]);
    }

    else {
      printf("failed to parse argument: %s\n", argv[i]);
      return openni::STATUS_ERROR;
    }
  }

  if(listDevices) {
    openni::Array<openni::DeviceInfo> deviceInfoList;
    openni::OpenNI::enumerateDevices(&deviceInfoList);
    printf("Number of available devices: %d\n", deviceInfoList.getSize());
    for(int i = 0; i < deviceInfoList.getSize(); i++) {
      openni::DeviceInfo deviceInfo = deviceInfoList[i];
      printf("Device %d\n", i);
      printf("  Name: %s\n", deviceInfo.getName());
      printf("  URI: %s\n", deviceInfo.getUri());
      printf("  USB Product ID: %04x\n", deviceInfo.getUsbProductId());
      printf("  USB Vendor ID: %04x\n", deviceInfo.getUsbVendorId());
      printf("  Vendor: %s\n", deviceInfo.getVendor());
      printf("\n");
    }
    exit(0);
  }

  status = device.open(deviceUri);
  if(status != openni::STATUS_OK) {
    printf("Failed to open device\n%s\n", openni::OpenNI::getExtendedError());
    return status;
  }

  status = depthStream.create(device, openni::SENSOR_DEPTH);
  if (status == openni::STATUS_OK) {
    if(deviceUri == NULL) {
      openni::VideoMode depthMode = depthStream.getVideoMode();
      depthMode.setFps(fps);
      depthMode.setResolution(640, 480);
      depthMode.setPixelFormat(openni::PIXEL_FORMAT_DEPTH_1_MM);
      status = depthStream.setVideoMode(depthMode);
    }
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

  oniWidth = depthStream.getVideoMode().getResolutionX();
  oniHeight = depthStream.getVideoMode().getResolutionY();
  if(resolutionX == 0)
    resolutionX = oniWidth;
  if(resolutionY == 0)
    resolutionY = oniHeight;

  transmitSocket = new UdpTransmitSocket(IpEndpointName(DEFAULT_OSC_HOST, OSC_PORT));

  calculateWorldRange();
  textureRenderer = NULL;
  initOpenGL(argc, argv);
  processingEnabled = true;
  processingMethod = new BlobTracker(this);
  depthFrame.create(resolutionY, resolutionX, CV_8UC1);
  zThresholdedDepthFrame.create(resolutionY, resolutionX, CV_8UC1);
  displayDepth = true;
  displayZThresholding = true;

  return openni::STATUS_OK;
}

void Tracker::calculateWorldRange() {
  float x1, x2, y1, y2, worldZ;
  openni::CoordinateConverter::convertDepthToWorld(depthStream, 0, 0, zThreshold,
						   &x1, &y1, &worldZ);
  openni::CoordinateConverter::convertDepthToWorld(depthStream, oniWidth, oniHeight, zThreshold,
						   &x2, &y2, &worldZ);
  worldRange.xMin = MIN(x1, x2);
  worldRange.xMax = MAX(x1, x2);
  worldRange.yMin = MIN(y1, y2);
  worldRange.yMax = MAX(y1, y2);
}

void Tracker::mainLoop() {
  previousDisplayTime = 0;
  glutMainLoop();
}

void Tracker::processOniDepthFrame() {
  const openni::DepthPixel* oniData =
    (const openni::DepthPixel*) oniDepthFrame.getData();
  int oniRowSize = oniDepthFrame.getStrideInBytes() / sizeof(openni::DepthPixel);
  uchar depth, zThresholdedDepth;
  uchar *depthFramePtr, *zThresholdedDepthFramePtr;
  float worldX, worldY, worldZ;

  for (int y = 0; y < resolutionY; ++y) {
    size_t oniY = (size_t) y * oniHeight / resolutionY;
    const openni::DepthPixel* pOniRow = oniData + oniY * oniRowSize;
    depthFramePtr = depthFrame.ptr(y);
    zThresholdedDepthFramePtr = zThresholdedDepthFrame.ptr(y);
    for (int x = 0; x < resolutionX; ++x) {
      size_t oniX = (size_t) x * oniWidth / resolutionX;
      const openni::DepthPixel* pOni = pOniRow + oniX;
      if (*pOni != 0) {
        depth = (int) (255 * (1 - float(*pOni) / MAX_DEPTH));
        openni::CoordinateConverter::convertDepthToWorld(depthStream, oniX, oniY, *pOni,
							 &worldX, &worldY, &worldZ);
        if(zThreshold > 0 && worldZ > zThreshold)
          zThresholdedDepth = 0;
        else
          zThresholdedDepth = depth;
      }
      else {
        depth = 0;
        zThresholdedDepth = 0;
      }
      *depthFramePtr++ = depth;
      *zThresholdedDepthFramePtr++ = zThresholdedDepth;
    }
  }
}

void Tracker::onWindowResized(int width, int height)
{
  windowWidth = width;
  windowHeight = height;
  glViewport(0, 0, windowWidth, windowHeight);
}

void Tracker::display()
{
  struct timeval tv;
  uint64_t currentDisplayTime, timeDiff;
  gettimeofday(&tv, NULL);
  currentDisplayTime = (uint64_t) (tv.tv_sec * 1000000 + tv.tv_usec);
  if(previousDisplayTime != 0) {
    timeDiff = currentDisplayTime - previousDisplayTime;
    log("time diff: %ld\n", timeDiff);
  }
  previousDisplayTime = currentDisplayTime;

  if(!paused) {
    openni::Status status = depthStream.readFrame(&oniDepthFrame);
    if (status != openni::STATUS_OK) {
      printf("Couldn't read depth frame:\n%s\n", openni::OpenNI::getExtendedError());
    }

    if(!oniDepthFrame.isValid())
      return;

    processOniDepthFrame();

    if(processingEnabled)
      processingMethod->processDepthFrame(zThresholdedDepthFrame);
  }

  if(textureRenderer == NULL) {
    textureRenderer = new TextureRenderer(resolutionX, resolutionY, depthAsPoints);
  }

  glClear (GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT);

  if(displayDepth)
    drawDepthFrame();

  if(processingEnabled) {
    glMatrixMode(GL_PROJECTION);
    glLoadIdentity();
    glOrtho(0, resolutionX, resolutionY, 0, -1.0, 1.0);
    glMatrixMode(GL_MODELVIEW);
    processingMethod->render();
  }

  glutSwapBuffers();

  checkGlErrors();
  log("Display done\n");
}

void Tracker::drawDepthFrame() {
  if(displayZThresholding)
    textureRenderer->drawCvImage(zThresholdedDepthFrame);
  else
    textureRenderer->drawCvImage(depthFrame);
}

void Tracker::glutIdle()
{
  log("glutIdle\n");
  glutPostRedisplay();
}

void Tracker::glutReshape(int width, int height) {
  Tracker::self->onWindowResized(width, height);
}

void Tracker::glutDisplay() {
  Tracker::self->display();
}

void Tracker::glutKeyboard(unsigned char key, int x, int y) {
  Tracker::self->onKey(key);
}

openni::Status Tracker::initOpenGL(int argc, char **argv)
{
  glutInit(&argc, argv);
  glutInitDisplayMode(GLUT_RGB | GLUT_DOUBLE | GLUT_DEPTH);
  glutInitWindowSize(GL_WIN_SIZE_X, GL_WIN_SIZE_Y);
  glutCreateWindow ("Tracker");
  glutSetCursor(GLUT_CURSOR_NONE);

  initOpenGLHooks();

  glDisable(GL_DEPTH_TEST);
  glEnable(GL_TEXTURE_2D);

  glEnableClientState(GL_VERTEX_ARRAY);
  glDisableClientState(GL_COLOR_ARRAY);

  return openni::STATUS_OK;
}

void Tracker::initOpenGLHooks()
{
  glutKeyboardFunc(glutKeyboard);
  glutDisplayFunc(glutDisplay);
  glutIdleFunc(glutIdle);
  glutReshapeFunc(glutReshape);
}

void Tracker::onKey(unsigned char key) {
  const static unsigned char TAB = 9;

  switch(key) {
  case TAB:
    processingEnabled = !processingEnabled;
    break;

  case 'd':
    displayDepth = !displayDepth;
    break;

  case 'z':
    displayZThresholding = !displayZThresholding;
    break;

  case ' ':
    paused = !paused;
    break;
  }

  if(processingEnabled)
    processingMethod->onKey(key);
}

ProcessingMethod::ProcessingMethod(Tracker *tracker) {
  this->tracker = tracker;
  width = tracker->getResolutionX();
  height = tracker->getResolutionY();
}

int main(int argc, char **argv) {
  Tracker tracker;
  openni::Status status = tracker.init(argc, argv);
  if (status != openni::STATUS_OK)
    return 1;
  tracker.mainLoop();
}
