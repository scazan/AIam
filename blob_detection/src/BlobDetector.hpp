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

#define TRUNCATE_THRESHOLD 10

class BlobDetector: public ProcessingMethod {
public:
  BlobDetector(Tracker *tracker) :
      ProcessingMethod(tracker) {
    float worldWidth = tracker->getWorldRange().xMax - tracker->getWorldRange().xMin;
    float worldHeight = tracker->getWorldRange().yMax - tracker->getWorldRange().yMin;
    worldArea = worldWidth * worldHeight;
    resolutionArea = width * height;
    orientationEstimationEnabled = false;
    recallEnabled = false;
    croppedTextureRenderer = new TextureRenderer(CROPPED_WIDTH, CROPPED_HEIGHT, tracker->depthAsPoints);
    cropX1 = (float)(width - CROPPED_WIDTH) / 2 / width;
    cropX2 = 1 - cropX1;
    cropY1 = (float)(height - CROPPED_HEIGHT) / 2 / height;
    cropY2 = 1 - cropY1;
  }

  void processDepthFrame(Mat& depthFrame) {
    std::vector<std::vector<Point> > unfilteredContours;
    Mat binaryImage;
    threshold(depthFrame, binaryImage, 1, 255, THRESH_BINARY);
    findContours(binaryImage, unfilteredContours, RETR_LIST, CHAIN_APPROX_NONE);
    filterContours(unfilteredContours);

    blobs.clear();
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
    bool isTruncated = false;
    Mat blobImage(height, width, CV_8UC1, 255);
    for (vector<Point>::const_iterator i = contour.begin(); i != contour.end();
        i++) {
      if(i->y <= TRUNCATE_THRESHOLD || i->y >= height-TRUNCATE_THRESHOLD || i->x <= TRUNCATE_THRESHOLD  || i->x >= width-TRUNCATE_THRESHOLD)
	isTruncated = true;
      blobImage.at < uchar > (i->y, i->x) = 0;
    }
    floodFill(blobImage, Point(0, 0), 0);

    Blob blob;
    blob.image = blobImage;
    Moments m = moments(contour);
    blob.centroidX = (int) (m.m10 / m.m00);
    blob.centroidY = (int) (m.m01 / m.m00);
    blobs.push_back(blob);

    if(!isTruncated) {
      int offsetX = blob.centroidX - CROPPED_WIDTH/2;
      int offsetY = blob.centroidY - CROPPED_HEIGHT/2;

      Mat croppedBlobImage(CROPPED_HEIGHT, CROPPED_WIDTH, CV_8UC1, 255);
      int croppedX, croppedY;
      for (vector<Point>::const_iterator i = contour.begin(); i != contour.end();
	   i++) {
	croppedX = i->x - offsetX;
	croppedY = i->y - offsetY;
	if(croppedX >= 0 && croppedX < CROPPED_WIDTH && croppedY >= 0 && croppedY < CROPPED_HEIGHT)
	  croppedBlobImage.at < uchar > (croppedY, croppedX) = 0;
      }

      floodFill(croppedBlobImage, Point(0, 0), 0);
      observations.push_back(croppedBlobImage);
    }
  }

  void render() {
    glDisable(GL_BLEND);
    for (vector<vector<Point> >::iterator i = contours.begin();
        i != contours.end(); i++) {
      drawContour(*i);
      if(orientationEstimationEnabled)
	drawEstimatedOrientation(*i);
    }

    glEnable(GL_BLEND);
    glBlendFunc(GL_SRC_COLOR, GL_DST_COLOR);

    Scalar color = Scalar(1, 0, 0);
    for (vector<Blob>::iterator i = blobs.begin(); i != blobs.end();
	 i++) {
      tracker->getTextureRenderer()->drawCvImage(i->image, 0, 0, 1, 1, color);
    }

    glDisable(GL_BLEND);
    for (vector<Blob>::iterator i = blobs.begin(); i != blobs.end();
	 i++) {
      drawCentroid(i->centroidX, i->centroidY);
    }

    if(recallEnabled && observations.size() > 0) {
      glEnable(GL_BLEND);
      glBlendFunc(GL_SRC_COLOR, GL_DST_COLOR);
      int randomObservationIndex = (int) ((float)random() / RAND_MAX * observations.size());
      croppedTextureRenderer->drawCvImage(observations[randomObservationIndex],
					  cropX1, cropY1, cropX2, cropY2);
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

  void drawCentroid(int x, int y) {
    glColor3f(0, 0, 1);
    glPointSize(5);
    glBegin(GL_POINTS);
    glVertex2i(x, y);
    glEnd();
  }

  void onKey(unsigned char key) {
    switch(key) {
    case 'o':
      orientationEstimationEnabled = !orientationEstimationEnabled;
      break;

    case 'r':
      recallEnabled = !recallEnabled;
      break;
    }
  }

private:
  class Blob {
  public:
    Mat image;
    int centroidX, centroidY;
  };

  float worldArea;
  float resolutionArea;
  std::vector<std::vector<Point> > contours;
  vector<Blob> blobs;
  vector<Mat> observations;
  bool orientationEstimationEnabled;
  bool recallEnabled;
  TextureRenderer *croppedTextureRenderer;
  float cropX1, cropY1, cropX2, cropY2;
};
