#include "DenseOpticalFlow.hpp"
#include <opencv2/imgproc/imgproc.hpp>

#if (ONI_PLATFORM == ONI_PLATFORM_MACOSX)
#include <GLUT/glut.h>
#else
#include <GL/glut.h>
#endif

DenseOpticalFlow::DenseOpticalFlow(int width, int height, int depthThreshold) :
  ProcessingMethod(width, height, depthThreshold) {}

void DenseOpticalFlow::processDepthFrame(openni::VideoFrameRef depthFrame) {
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

  if(!previousFrame.empty()) {
    calcOpticalFlowFarneback(previousFrame, frame, flow,
			     0.5, 3, 15, 3, 5, 1.2, 0);
  }

  cv::swap(previousFrame, frame);
}

void DenseOpticalFlow::render() {
  if(flow.empty())
    return;

  glColor3f(0, 255, 0);
  glPointSize(3);
  glBegin(GL_POINTS);
  Point2f point;

  const int step = 20;

  for(int y = step/2; y < height; y += step) {
    for(int x = step/2; x < width; x += step) {
      point = flow.at<Point2f>(y, x);
      glVertex2f((float)(x + point.x) / width,
		 (float)(y + point.y) / height);
    }
  }

  glEnd();
}
