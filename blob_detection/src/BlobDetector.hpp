#include <vector>

using namespace std;

#if (ONI_PLATFORM == ONI_PLATFORM_MACOSX)
#include <GLUT/glut.h>
#else
#include <GL/glut.h>
#endif

#define MIN_BLOB_AREA 50000
#define MAX_BLOB_AREA 1000000

class BlobDetector: public ProcessingMethod {
public:
  BlobDetector(Tracker *tracker) :
      ProcessingMethod(tracker) {
    float worldWidth = tracker->getWorldRange().xMax - tracker->getWorldRange().xMin;
    float worldHeight = tracker->getWorldRange().yMax - tracker->getWorldRange().yMin;
    worldArea = worldWidth * worldHeight;
    resolutionArea = width * height;
    orientationEstimationEnabled = false;
  }

  void processDepthFrame(Mat& depthFrame) {
    std::vector<std::vector<Point> > unfilteredContours;
    Mat binaryImage;
    threshold(depthFrame, binaryImage, 1, 255, THRESH_BINARY);
    findContours(binaryImage, unfilteredContours, RETR_LIST, CHAIN_APPROX_NONE);
    filterContours(unfilteredContours);

    blobImages.clear();
    for (vector<vector<Point> >::iterator i = contours.begin();
        i != contours.end(); i++) {
      processContour(*i);
    }
  }

  void filterContours(std::vector<std::vector<Point> > &unfilteredContours) {
    contours.clear();
    for (vector<vector<Point> >::iterator i = unfilteredContours.begin();
        i != unfilteredContours.end(); i++) {
      float pixelArea = contourArea(*i);
      float area = pixelArea / resolutionArea * worldArea;
      if (area >= MIN_BLOB_AREA && area <= MAX_BLOB_AREA) {
        contours.push_back(*i);
      }
    }
  }

  void processContour(const vector<Point>& contour) {
    Mat blobImage(height, width, CV_8UC1, 255);
    for (vector<Point>::const_iterator i = contour.begin(); i != contour.end();
        i++) {
      blobImage.at < uchar > (i->y, i->x) = 0;
    }

    floodFill(blobImage, Point(0, 0), 0);
    blobImages.push_back(blobImage);
  }

  void render() {
    for (vector<vector<Point> >::iterator i = contours.begin();
        i != contours.end(); i++) {
      drawContour(*i);
      if(orientationEstimationEnabled)
	drawEstimatedOrientation(*i);
    }

    Scalar color = Scalar(1, 0, 0);
    for (vector<Mat>::iterator i = blobImages.begin(); i != blobImages.end();
        i++) {
      tracker->drawCvImage(*i, color);
    }
  }

  void drawContour(const vector<Point>& contour) {
    glColor3f(0, 0, 1);
    glBegin (GL_LINE_LOOP);
    for (vector<Point>::const_iterator i = contour.begin(); i != contour.end();
        i++) {
      glVertex2i(i->x, i->y);
    }
    glEnd();
  }

  void drawEstimatedOrientation(const vector<Point>& contour) {
    glColor3f(0, 0, 1);
    Vec4f v;
    fitLine(contour, v, CV_DIST_L2, 0, 0.1, 0.1);
    float vx = v[0];
    float vy = v[1];
    float x = v[2];
    float y = v[3];
    float leftY = -x * vy / vx + y;
    float rightY = (width - x) * vy / vx + y;
    glColor3f(0, 1, 0);
    glBegin(GL_LINES);
    glVertex2i(0, leftY);
    glVertex2i(width-1, rightY);
    glEnd();
  }

  void onKey(unsigned char key) {
    switch(key) {
    case 'o':
      orientationEstimationEnabled = !orientationEstimationEnabled;
      break;
    }
  }

private:
  float worldArea;
  float resolutionArea;
  std::vector<std::vector<Point> > contours;
  vector<Mat> blobImages;
  bool orientationEstimationEnabled;
};
