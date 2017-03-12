#include <vector>

using namespace std;

#if (ONI_PLATFORM == ONI_PLATFORM_MACOSX)
#include <GLUT/glut.h>
#else
#include <GL/glut.h>
#endif

#define MIN_BLOB_AREA 50000
#define MAX_BLOB_AREA 1000000

#define CROPPED_WIDTH 400
#define CROPPED_HEIGHT 400

class BlobDetector: public ProcessingMethod {
public:
  BlobDetector(Tracker *tracker) :
      ProcessingMethod(tracker) {
    float worldWidth = tracker->getWorldRange().xMax - tracker->getWorldRange().xMin;
    float worldHeight = tracker->getWorldRange().yMax - tracker->getWorldRange().yMin;
    worldArea = worldWidth * worldHeight;
    resolutionArea = width * height;
    orientationEstimationEnabled = false;
    croppingEnabled = false;
    croppedTextureRenderer = new TextureRenderer(CROPPED_WIDTH, CROPPED_HEIGHT, tracker->depthAsPoints);
  }

  void processDepthFrame(Mat& depthFrame) {
    std::vector<std::vector<Point> > unfilteredContours;
    Mat binaryImage;
    threshold(depthFrame, binaryImage, 1, 255, THRESH_BINARY);
    findContours(binaryImage, unfilteredContours, RETR_LIST, CHAIN_APPROX_NONE);
    filterContours(unfilteredContours);

    blobImages.clear();
    croppedBlobImages.clear();
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

    Moments m = moments(contour);
    int centroidX = (int) (m.m10 / m.m00);
    int centroidY = (int) (m.m01 / m.m00);
    int offsetX = width/2 - centroidX;
    int offsetY = height/2 - centroidY;

    Mat croppedBlobImage(CROPPED_HEIGHT, CROPPED_WIDTH, CV_8UC1, 255);
    int croppedX, croppedY;
    for (vector<Point>::const_iterator i = contour.begin(); i != contour.end();
        i++) {
      croppedX = i->x + offsetX;
      croppedY = i->y + offsetY;
      if(croppedX >= 0 && croppedX < CROPPED_WIDTH && croppedY >= 0 && croppedY < CROPPED_HEIGHT)
	croppedBlobImage.at < uchar > (croppedY, croppedX) = 0;
    }

    floodFill(croppedBlobImage, Point(0, 0), 0);
    croppedBlobImages.push_back(croppedBlobImage);
  }

  void render() {
    for (vector<vector<Point> >::iterator i = contours.begin();
        i != contours.end(); i++) {
      drawContour(*i);
      if(orientationEstimationEnabled)
	drawEstimatedOrientation(*i);
    }

    if(croppingEnabled) {
      for (vector<Mat>::iterator i = croppedBlobImages.begin(); i != croppedBlobImages.end();
	   i++) {
	croppedTextureRenderer->drawCvImage(*i);
      }
    }
    else {
      Scalar color = Scalar(1, 0, 0);
      for (vector<Mat>::iterator i = blobImages.begin(); i != blobImages.end();
	   i++) {
	tracker->getTextureRenderer()->drawCvImage(*i, color);
      }
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

    case 'c':
      croppingEnabled = !croppingEnabled;
      break;
    }
  }

private:
  float worldArea;
  float resolutionArea;
  std::vector<std::vector<Point> > contours;
  vector<Mat> blobImages;
  vector<Mat> croppedBlobImages;
  bool orientationEstimationEnabled;
  bool croppingEnabled;
  TextureRenderer *croppedTextureRenderer;
};
