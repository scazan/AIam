#ifndef _LUCAS_KANADE_HPP_
#define _LUCAS_KANADE_HPP_

#include "Tracker.hpp"
#include <opencv2/video/tracking.hpp>
#include <opencv2/imgproc/imgproc.hpp>

using namespace cv;

class LucasKanadeOpticalFlow : public ProcessingMethod {
public:
  LucasKanadeOpticalFlow(Tracker *tracker);
  void processDepthFrame(Mat&);
  void render();
  void onKey(unsigned char key);

private:
  Mat frame, previousFrame;
  bool needToInit;
  vector<Point2f> points[2];
  vector<uchar> status;
};

#endif
