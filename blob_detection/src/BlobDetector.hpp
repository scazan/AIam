#include <opencv2/features2d/features2d.hpp>
#include <vector>

using namespace std;

#if (ONI_PLATFORM == ONI_PLATFORM_MACOSX)
#include <GLUT/glut.h>
#else
#include <GL/glut.h>
#endif

class BlobDetector : public ProcessingMethod {
public:
  BlobDetector(int width, int height) : ProcessingMethod(width, height) {
    SimpleBlobDetector::Params params;
    params.filterByColor = false;
    params.filterByArea = true;
    params.minArea = 65*65;
    params.maxArea = 180*180;
    params.filterByCircularity = false;
    params.filterByInertia = false;
    params.filterByConvexity = false;

    detector = new SimpleBlobDetector(params);
  }

  void processDepthFrame(Mat& frame) {
    detector->detect(frame, keyPoints);
  }

  void render() {
    glColor3f(0,1,0);
    for(vector<KeyPoint>::iterator i = keyPoints.begin(); i != keyPoints.end(); i++) {
      drawCircle(i->pt.x / width, i->pt.y / height, i->size / 2 / width);
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

  void onKey(unsigned char key) {}

private:
  SimpleBlobDetector *detector;
  std::vector<KeyPoint> keyPoints;
};
