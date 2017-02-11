#include <vector>

using namespace std;

#if (ONI_PLATFORM == ONI_PLATFORM_MACOSX)
#include <GLUT/glut.h>
#else
#include <GL/glut.h>
#endif

class BlobDetector : public ProcessingMethod {
public:
  BlobDetector(Tracker *tracker) : ProcessingMethod(tracker) {
  }

  void processDepthFrame(Mat& depthFrame) {
    Mat binaryImage;
    threshold(depthFrame, binaryImage, 1, 255, THRESH_BINARY);
    findContours(binaryImage, contours, RETR_LIST, CHAIN_APPROX_NONE);
    blobImages.clear();
    for(vector< vector<Point> >::iterator i = contours.begin(); i != contours.end(); i++)
      processContour(*i);
  }

  void processContour(const vector<Point>& contour) {
    Mat blobImage = Mat::ones(height, width, CV_8UC1);
    for (vector<Point>::const_iterator i = contour.begin(); i != contour.end();
        i++) {
      blobImage.at<uchar>(i->y, i->x) = 0;
    }

    floodFill(blobImage, Point(0,0), 0);
    blobImages.push_back(blobImage);
  }

  void render() {
    glColor3f(0,0,1);
    for(vector< vector<Point> >::iterator i = contours.begin(); i != contours.end(); i++) {
      drawContour(*i);
    }

    glColor3f(1,0,0);
    for(vector<Mat>::iterator i = blobImages.begin(); i != blobImages.end(); i++) {
      drawBlobImage(*i);
    }
  }

  void drawContour(const vector<Point>& contour) {
    glBegin(GL_LINE_LOOP);
    for(vector<Point>::const_iterator i = contour.begin(); i != contour.end(); i++) {
      glVertex2f((float)i->x / width, (float)i->y / height);
    }
    glEnd();
  }

  void drawBlobImage(Mat image) {
    uchar *matPtr;
    glBegin (GL_POINTS);
    for (int y = 0; y < height; y++) {
      matPtr = image.ptr(y);
      for (int x = 0; x < width; x++, matPtr++) {
        if (*matPtr) {
          glVertex2f((float) x / width, (float) y / height);
        }
      }
    }
    glEnd();
  }

  void onKey(unsigned char key) {}

private:
  std::vector < std::vector<Point> > contours;
  vector<Mat> blobImages;
};
