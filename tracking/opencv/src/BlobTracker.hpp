#include <vector>

using namespace std;

#if (ONI_PLATFORM == ONI_PLATFORM_MACOSX)
#include <GLUT/glut.h>
#else
#include <GL/glut.h>
#endif

#define DEFAULT_MIN_BLOB_AREA 100000
#define DEFAULT_MAX_BLOB_AREA 1000000

#ifndef USE_GLES
void glPrintString(void *font, const char *str) {
  int i, l = (int)strlen(str);
  for(i=0; i<l; i++) {   
    glutBitmapCharacter(font,*str++);
  }   
}
#endif

class BlobTracker: public ProcessingMethod {
private:
  class Blob {
  public:
    int id;
    bool paired;
    Mat image;
    int centroidX, centroidY;
  };

  float worldArea;
  float resolutionArea;
  std::vector<std::vector<Point> > contours;
  vector<Blob> blobsInFrame;
  vector<Blob> trackedBlobs;
  bool orientationEstimationEnabled;
  bool displayBlobs;
  char oscBuffer[OSC_BUFFER_SIZE];
  int idCount;

public:
  BlobTracker(Tracker *tracker) :
      ProcessingMethod(tracker) {
    float worldWidth = tracker->getWorldRange().xMax - tracker->getWorldRange().xMin;
    float worldHeight = tracker->getWorldRange().yMax - tracker->getWorldRange().yMin;
    worldArea = worldWidth * worldHeight;
    resolutionArea = width * height;
    orientationEstimationEnabled = false;
    displayBlobs = true;
    idCount = 0;
  }

  void processDepthFrame(Mat& depthFrame) {
    std::vector<std::vector<Point> > unfilteredContours;
    Mat binaryImage;
    threshold(depthFrame, binaryImage, 1, 255, THRESH_BINARY);
    findContours(binaryImage, unfilteredContours, RETR_LIST, CHAIN_APPROX_NONE);
    filterContours(unfilteredContours);

    blobsInFrame.clear();
    for (vector<vector<Point> >::iterator i = contours.begin();
        i != contours.end(); i++) {
      processContour(*i);
    }

    updateTrackedBlobs();
  }

  void filterContours(std::vector<std::vector<Point> > &unfilteredContours) {
    contours.clear();
    for (vector<vector<Point> >::iterator i = unfilteredContours.begin();
        i != unfilteredContours.end(); i++) {
      float pixelArea = contourArea(*i);
      float area = pixelArea / resolutionArea * worldArea;
      if (area >= tracker->minBlobArea && area <= tracker->maxBlobArea) {
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

    Blob blob;
    blob.image = blobImage;
    Moments m = moments(contour);
    blob.centroidX = (int) (m.m10 / m.m00);
    blob.centroidY = (int) (m.m01 / m.m00);
    blobsInFrame.push_back(blob);
  }

  void updateTrackedBlobs() {
    for (vector<Blob>::iterator trackedBlob = trackedBlobs.begin();
	 trackedBlob != trackedBlobs.end();
	 trackedBlob++) {
      trackedBlob->paired = false;
    }
    
    for (vector<Blob>::iterator blobInFrame = blobsInFrame.begin();
	 blobInFrame != blobsInFrame.end();
	 blobInFrame++) {
      vector<Blob>::iterator nearestTrackedBlob = getNearestTrackedBlob(*blobInFrame);
      if(nearestTrackedBlob == trackedBlobs.end()) {
	addTrackedBlob(*blobInFrame);
      }
      else {
	nearestTrackedBlob->centroidX = blobInFrame->centroidX;
	nearestTrackedBlob->centroidY = blobInFrame->centroidY;
	sendCenter(*nearestTrackedBlob);
      }
    }

    vector<vector<Blob>::iterator> unpairedTrackedBlobs;
    for (vector<Blob>::iterator trackedBlob = trackedBlobs.begin();
	 trackedBlob != trackedBlobs.end();
	 trackedBlob++) {
      if(!trackedBlob->paired)
	unpairedTrackedBlobs.push_back(trackedBlob);
    }
    for(vector<vector<Blob>::iterator>::reverse_iterator unpairedTrackedBlob = unpairedTrackedBlobs.rbegin();
	unpairedTrackedBlob != unpairedTrackedBlobs.rend();
	unpairedTrackedBlob++) {
      deleteTrackedBlob(*unpairedTrackedBlob);
    }
  }

  vector<Blob>::iterator getNearestTrackedBlob(const Blob& blob) {
    vector<Blob>::iterator nearestTrackedBlob = trackedBlobs.end();
    float shortestDistance = 0;
    for (vector<Blob>::iterator trackedBlob = trackedBlobs.begin();
	 trackedBlob != trackedBlobs.end();
	 trackedBlob++) {
      if(!trackedBlob->paired) {
	bool isNearest = false;
	float distance = blobDistance(blob, *trackedBlob);
	if(nearestTrackedBlob == trackedBlobs.end()) {
	  isNearest = true;
	}
	else if(distance < shortestDistance) {
	  isNearest = true;
	}
	if(isNearest) {
	  nearestTrackedBlob = trackedBlob;
	  shortestDistance = distance;
	  trackedBlob->paired = true;
	}
      }
    }
    return nearestTrackedBlob;
  }

  float blobDistance(const Blob& b1, const Blob& b2) {
    float dx = b1.centroidX - b2.centroidX;
    float dy = b1.centroidY - b2.centroidY;
    return sqrt(dx*dx + dy*dy);
  }
  
  void addTrackedBlob(const Blob& blob) {
    Blob trackedBlob = blob;
    trackedBlob.paired = true;
    trackedBlob.id = idCount++;
    trackedBlobs.push_back(trackedBlob);
    sendState(trackedBlob.id, "new");
  }

  void deleteTrackedBlob(vector<Blob>::iterator blob) {
    sendState(blob->id, "lost");
    trackedBlobs.erase(blob);
  }
  
  void render() {
    if(displayBlobs) {
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
      for (vector<Blob>::iterator i = blobsInFrame.begin(); i != blobsInFrame.end();
	   i++) {
	tracker->getTextureRenderer()->drawCvImage(i->image, 0, 0, 1, 1, color);
      }

      glDisable(GL_BLEND);
      for (vector<Blob>::iterator i = blobsInFrame.begin(); i != blobsInFrame.end();
	   i++) {
	drawCentroid(i->centroidX, i->centroidY);
      }

      for (vector<Blob>::iterator i = trackedBlobs.begin(); i != trackedBlobs.end();
	   i++) {
	drawId(i->centroidX, i->centroidY, i->id);
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

  void drawCentroid(int x, int y) {
    glColor3f(0, 0, 1);
    glPointSize(5);
    glBegin(GL_POINTS);
    glVertex2i(x, y);
    glEnd();
  }

  void drawId(int x, int y, int id) {
    static char string[1024];
    sprintf(string, "%d", id);
    glColor3f(0, 0, 1);
    glRasterPos2f(x, y);
    glPrintString(GLUT_BITMAP_HELVETICA_18, string);
  }

  void sendState(int id, const char *state) {
    printf("%s %d\n", state, id);
    osc::OutboundPacketStream stream(oscBuffer, OSC_BUFFER_SIZE);
    stream << osc::BeginBundleImmediate
	   << osc::BeginMessage("/state") << id << state
	   << osc::EndMessage
	   << osc::EndBundle;
    tracker->transmitSocket->Send(stream.Data(), stream.Size());
  }
  
  void sendCenter(const Blob& blob) {
    float depthZ = 0;
    float x, y, z;
    openni::CoordinateConverter::convertDepthToWorld(tracker->getDepthStream(),
						     blob.centroidX, blob.centroidY, tracker->zThreshold,
						     &x, &y, &z);
    osc::OutboundPacketStream stream(oscBuffer, OSC_BUFFER_SIZE);
    stream << osc::BeginBundleImmediate
	   << osc::BeginMessage("/center") << blob.id << x << y << z
	   << osc::EndMessage
	   << osc::EndBundle;
    tracker->transmitSocket->Send(stream.Data(), stream.Size());
  }

  void onKey(unsigned char key) {
    switch(key) {
    case 'o':
      orientationEstimationEnabled = !orientationEstimationEnabled;
      break;

    case 'b':
      displayBlobs = !displayBlobs;
      break;
    }
  }
};
