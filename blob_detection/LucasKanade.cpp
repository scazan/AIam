#include "LucasKanade.hpp"

#if (ONI_PLATFORM == ONI_PLATFORM_MACOSX)
#include <GLUT/glut.h>
#else
#include <GL/glut.h>
#endif

LucasKanadeOpticalFlow::LucasKanadeOpticalFlow(int depthThreshold) : ProcessingMethod(depthThreshold) {
  needToInit = false;
}

void LucasKanadeOpticalFlow::OnKey(unsigned char key) {
  switch (key)
    {
    case 'r':
      needToInit = true;
      break;
    }
}

void LucasKanadeOpticalFlow::processDepthFrame(openni::VideoFrameRef depthFrame) {
  if(cvFrame.empty()) {
    width = depthFrame.getWidth();
    height = depthFrame.getHeight();
    cvFrame.create(height, width, CV_8UC1);
  }

  const openni::DepthPixel* pDepthRow = (const openni::DepthPixel*)depthFrame.getData();
  int rowSize = depthFrame.getStrideInBytes() / sizeof(openni::DepthPixel);
  uchar depth_255;

  for (int y = 0; y < height; ++y)
    {
      const openni::DepthPixel* pDepth = pDepthRow;

      for (int x = 0; x < width; ++x, ++pDepth)
	{
	  if (*pDepth != 0 && *pDepth < depthThreshold)
	    {
	      depth_255 = (int) (255 * (1 - float(*pDepth) / depthThreshold));
	    }
	  else {
	    depth_255 = 0;
	  }

	  cvFrame.at<uchar>(y, x) = depth_255; // TODO: optimize?
	}

      pDepthRow += rowSize;
    }

  const int MAX_COUNT = 500;
  TermCriteria termcrit(CV_TERMCRIT_ITER|CV_TERMCRIT_EPS, 20, 0.03); // only once?
  Size subPixWinSize(10,10), winSize(31,31); // only once?

  if( needToInit )
    {
      // automatic initialization
      goodFeaturesToTrack(cvFrame, points[1], MAX_COUNT, 0.01, 10, Mat(), 3, 0, 0.04);
      cornerSubPix(cvFrame, points[1], subPixWinSize, Size(-1,-1), termcrit);
    }
  else if( !points[0].empty() )
    {
      vector<float> err;
      if(cvPreviousFrame.empty())
	cvFrame.copyTo(cvPreviousFrame);
      calcOpticalFlowPyrLK(cvPreviousFrame, cvFrame, points[0], points[1], status, err, winSize,
			   3, termcrit, 0, 0.001);
    }

  std::swap(points[1], points[0]);
  cv::swap(cvPreviousFrame, cvFrame);

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
