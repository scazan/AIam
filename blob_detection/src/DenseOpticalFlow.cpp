#include "DenseOpticalFlow.hpp"
#include <opencv2/imgproc/imgproc.hpp>

#if (ONI_PLATFORM == ONI_PLATFORM_MACOSX)
#include <GLUT/glut.h>
#else
#include <GL/glut.h>
#endif

#define TEXTURE_SIZE	512

#define MIN_NUM_CHUNKS(data_size, chunk_size)	((((data_size)-1) / (chunk_size) + 1))
#define MIN_CHUNKS_SIZE(data_size, chunk_size)	(MIN_NUM_CHUNKS(data_size, chunk_size) * (chunk_size))

DenseOpticalFlow::DenseOpticalFlow(int width, int height, int depthThreshold) :
    ProcessingMethod(width, height, depthThreshold) {
  gridMode = true;
}

void DenseOpticalFlow::onKey(unsigned char key) {
  switch (key) {
  case 'g':
    gridMode = !gridMode;
    break;
  }
}

void DenseOpticalFlow::processDepthFrame(Mat& newFrame) {
  newFrame.copyTo(frame);

  if (!previousFrame.empty()) {
    calcOpticalFlowFarneback(previousFrame, frame, flow, 0.5, 3, 15, 3, 5, 1.2,
        0);
  }

  cv::swap(previousFrame, frame);
}

void DenseOpticalFlow::render() {
  if (flow.empty())
    return;
  if (gridMode)
    renderAsGrid();
  else
    renderEntireFlow();
}

void DenseOpticalFlow::renderAsGrid() {
  glColor3f(0, 255, 0);
  glPointSize(3);
  glBegin(GL_POINTS);
  Point2f point;

  const int step = 20;

  for (int y = step / 2; y < height; y += step) {
    for (int x = step / 2; x < width; x += step) {
      point = flow.at<Point2f>(y, x);
      glVertex2f((float) (x + point.x) / width, (float) (y + point.y) / height);
    }
  }

  glEnd();
}

void DenseOpticalFlow::renderEntireFlow() {
  if (textureMap == NULL) {
    textureMapWidth = MIN_CHUNKS_SIZE(width, TEXTURE_SIZE);
    textureMapHeight = MIN_CHUNKS_SIZE(height, TEXTURE_SIZE);
    textureMap = new openni::RGB888Pixel[textureMapWidth * textureMapHeight];
  }

  Point2f point;
  float maxMovement = 0;
  for (int y = 0; y < height; y++) {
    for (int x = 0; x < width; x++) {
      point = flow.at<Point2f>(y, x); // TODO: optimize?
      maxMovement = MAX(maxMovement, sqrt(point.x*point.x + point.y*point.y));
    }
  }

  if (maxMovement <= 0)
    return;

  memset(textureMap, 0,
      textureMapWidth * textureMapHeight * sizeof(openni::RGB888Pixel));
  unsigned char c;
  openni::RGB888Pixel* textureMapRow = textureMap;
  for (int y = 0; y < height; y++) {
    openni::RGB888Pixel* pTex = textureMapRow;
    for (int x = 0; x < width; x++, pTex++) {
      point = flow.at<Point2f>(y, x); // TODO: optimize?
      c =
          (int) (255 * sqrt(point.x * point.x + point.y * point.y) / maxMovement);
      pTex->r = c;
      pTex->g = c;
      pTex->b = c;
    }
    textureMapRow += textureMapWidth;
  }

  glTexParameteri(GL_TEXTURE_2D, GL_GENERATE_MIPMAP_SGIS, GL_TRUE);
  glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER,
      GL_LINEAR_MIPMAP_LINEAR);
  glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR);
  glTexImage2D(GL_TEXTURE_2D, 0, GL_RGB, textureMapWidth, textureMapHeight, 0,
      GL_RGB, GL_UNSIGNED_BYTE, textureMap);

  // Display the OpenGL texture map
  glColor4f(1, 1, 1, 1);

  glEnable(GL_TEXTURE_2D);
  glBegin(GL_QUADS);

  // upper left
  glTexCoord2f(0, 0);
  glVertex2f(0, 0);
  // upper right
  glTexCoord2f((float) width / (float) textureMapWidth, 0);
  glVertex2f(1, 0);
  // bottom right
  glTexCoord2f((float) width / (float) textureMapWidth,
      (float) height / (float) textureMapHeight);
  glVertex2f(1, 1);
  // bottom left
  glTexCoord2f(0, (float) height / (float) textureMapHeight);
  glVertex2f(0, 1);

  glEnd();
  glDisable(GL_TEXTURE_2D);
}
