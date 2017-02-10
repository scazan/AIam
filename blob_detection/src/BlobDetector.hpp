#include <opencv2/features2d/features2d.hpp>
#include <vector>

using namespace std;

#if (ONI_PLATFORM == ONI_PLATFORM_MACOSX)
#include <GLUT/glut.h>
#else
#include <GL/glut.h>
#endif

#define MIN_BLOB_DIAMETER_MM 200
#define MAX_BLOB_DIAMETER_MM 1000

class BlobDetector : public ProcessingMethod {
public:
  BlobDetector(Tracker *tracker) : ProcessingMethod(tracker) {
    float worldWidth = tracker->getWorldRange().xMax - tracker->getWorldRange().xMin;
    float minWidth = MIN_BLOB_DIAMETER_MM * width / worldWidth;
    float maxWidth = MAX_BLOB_DIAMETER_MM * width / worldWidth;

    SimpleBlobDetector::Params params;
    params.filterByColor = false;
    params.filterByArea = true;
    params.minArea = minWidth*minWidth;
    params.maxArea = maxWidth*maxWidth;
    params.filterByCircularity = false;
    params.filterByInertia = false;
    params.filterByConvexity = false;

    detector = new SimpleBlobDetector(params);
  }

  void processDepthFrame(Mat& depthFrame) {
    Mat binaryImage;
    threshold(depthFrame, binaryImage, 1, 255, THRESH_BINARY);
    findContours(binaryImage, contours, RETR_LIST, CHAIN_APPROX_NONE);
    detector->detect(depthFrame, keyPoints);
  }

  void render() {
    glColor3f(0,1,0);
    for(vector<KeyPoint>::iterator i = keyPoints.begin(); i != keyPoints.end(); i++) {
      drawCircle(i->pt.x / width, i->pt.y / height, i->size / 2 / width);
    }

    glColor3f(0,0,1);
    for(vector< vector<Point> >::iterator i = contours.begin(); i != contours.end(); i++) {
      drawContour(*i);
    }
  }

  void drawCircle(float centerX, float centerY, float radius) {
    static const int RESOLUTION = 20;
    glBegin(GL_LINE_LOOP);
    float a, x, y;
    for(int i=0; i<RESOLUTION; i++) {
      a = 2 * M_PI * i/RESOLUTION;
      x = centerX + cos(a) * radius;
      y = centerY + sin(a) * radius;
      glVertex2f(x, y);
    }
    glEnd();
  }

  void drawContour(const vector<Point> contour) {
    glBegin(GL_LINE_LOOP);
    for(vector<Point>::const_iterator i = contour.begin(); i != contour.end(); i++) {
      glVertex2f((float)i->x / width, (float)i->y / height);
    }
    glEnd();
  }

  void onKey(unsigned char key) {}

private:
  SimpleBlobDetector *detector;
  std::vector<KeyPoint> keyPoints;
  std::vector < std::vector<Point> > contours;
};
