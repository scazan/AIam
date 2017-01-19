#include "LucasKanade.hpp"

#if (ONI_PLATFORM == ONI_PLATFORM_MACOSX)
#include <GLUT/glut.h>
#else
#include <GL/glut.h>
#endif

LucasKanadeOpticalFlow::LucasKanadeOpticalFlow(int width, int height, int depthThreshold) :
  ProcessingMethod(width, height, depthThreshold) {
  needToInit = false;
}

void LucasKanadeOpticalFlow::onKey(unsigned char key) {
  switch (key) {
  case 'r':
    needToInit = true;
    break;
  }
}

void LucasKanadeOpticalFlow::processDepthFrame(openni::VideoFrameRef depthFrame) {
  if(frame.empty())
    frame.create(height, width, CV_8UC1);

  const openni::DepthPixel* pOniRow = (const openni::DepthPixel*)depthFrame.getData();
  int rowSize = depthFrame.getStrideInBytes() / sizeof(openni::DepthPixel);
  uchar depth;
  uchar *pCv;

  for (int y = 0; y < height; ++y) {
    const openni::DepthPixel* pOni = pOniRow;
    pCv = frame.ptr(y);
    for (int x = 0; x < width; ++x, ++pOni) {
      if (*pOni != 0 && *pOni < depthThreshold)
	depth = (int) (255 * (1 - float(*pOni) / depthThreshold));
      else
	depth = 0;
      *pCv++ = depth;
    }
    pOniRow += rowSize;
  }

  const int MAX_COUNT = 500;
  TermCriteria termcrit(CV_TERMCRIT_ITER|CV_TERMCRIT_EPS, 20, 0.03); // only once?
  Size subPixWinSize(10,10), winSize(31,31); // only once?

  if(needToInit) {
    goodFeaturesToTrack(frame, points[1], MAX_COUNT, 0.01, 10, Mat(), 3, 0, 0.04);
    cornerSubPix(frame, points[1], subPixWinSize, Size(-1,-1), termcrit);
  }
  else if( !points[0].empty() ) {
    vector<float> err;
    if(previousFrame.empty())
      frame.copyTo(previousFrame);
    calcOpticalFlowPyrLK(previousFrame, frame, points[0], points[1], status, err, winSize,
			 3, termcrit, 0, 0.001);
  }

  std::swap(points[1], points[0]);
  cv::swap(previousFrame, frame);

  needToInit = false;
}

void LucasKanadeOpticalFlow::render() {
  glColor3f(0, 255, 0);
  glPointSize(3);
  glBegin(GL_POINTS);
  Point2f point;

  for(size_t i = 0; i < points[1].size(); i++ )
    {
      if( !status[i] )
	continue;
     point = points[1][i];
     glVertex2f(point.x / width, point.y / height);
    }

  glEnd();
}
