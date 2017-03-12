#if (ONI_PLATFORM == ONI_PLATFORM_MACOSX)
#include <GLUT/glut.h>
#else
#include <GL/glut.h>
#endif

#include <opencv2/imgproc/imgproc.hpp>

#define TEXTURE_SIZE        512

#define MIN_NUM_CHUNKS(data_size, chunk_size)        ((((data_size)-1) / (chunk_size) + 1))
#define MIN_CHUNKS_SIZE(data_size, chunk_size)        (MIN_NUM_CHUNKS(data_size, chunk_size) * (chunk_size))

using namespace cv;

class TextureRenderer {
public:
  TextureRenderer(int resolutionX, int resolutionY, bool depthAsPoints) {
    this->resolutionX = resolutionX;
    this->resolutionY = resolutionY;
    this->depthAsPoints = depthAsPoints;
    textureMapWidth = MIN_CHUNKS_SIZE(resolutionX, TEXTURE_SIZE);
    textureMapHeight = MIN_CHUNKS_SIZE(resolutionY, TEXTURE_SIZE);
    textureMap = new openni::RGB888Pixel[textureMapWidth * textureMapHeight];
  }

  ~TextureRenderer() {
    delete[] textureMap;
  }

  void drawCvImage(const Mat &image, const Scalar &color=Scalar(1,1,1)) {
    const uchar *matPtr;
    unsigned char c;
    openni::RGB888Pixel* textureMapRow = textureMap;
    for (int y = 0; y < resolutionY; y++) {
      matPtr = image.ptr(y);
      openni::RGB888Pixel* pTex = textureMapRow;
      for (int x = 0; x < resolutionX; x++, pTex++, matPtr++) {
	c = *matPtr;
	pTex->r = c * color[0];
	pTex->g = c * color[1];
	pTex->b = c * color[2];
      }
      textureMapRow += textureMapWidth;
    }

    glEnable(GL_BLEND);
    glBlendFunc(GL_SRC_COLOR, GL_DST_COLOR);

    glMatrixMode(GL_PROJECTION);
    glPushMatrix();
    glLoadIdentity();
    glOrtho(0, 1.0, 1.0, 0, -1.0, 1.0);
    glMatrixMode(GL_MODELVIEW);
    glLoadIdentity();

    if(depthAsPoints)
      drawTextureMapAsPoints();
    else
      drawTextureMapAsTexture();

    glMatrixMode(GL_PROJECTION);
    glPopMatrix();
  }

private:
  void drawTextureMapAsTexture() {
    glTexParameteri(GL_TEXTURE_2D, GL_GENERATE_MIPMAP_SGIS, GL_TRUE);
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR_MIPMAP_LINEAR);
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR);
    glTexImage2D(GL_TEXTURE_2D, 0, GL_RGB, textureMapWidth, textureMapHeight, 0, GL_RGB, GL_UNSIGNED_BYTE, textureMap);

    // Display the OpenGL texture map
    glColor4f(1,1,1,1);

    glEnable(GL_TEXTURE_2D);
    glBegin(GL_QUADS);

    // upper left
    glTexCoord2f(0, 0);
    glVertex2f(0, 0);
    // upper right
    glTexCoord2f((float)resolutionX/(float)textureMapWidth, 0);
    glVertex2f(1, 0);
    // bottom right
    glTexCoord2f((float)resolutionX/(float)textureMapWidth, (float)resolutionY/(float)textureMapHeight);
    glVertex2f(1, 1);
    // bottom left
    glTexCoord2f(0, (float)resolutionY/(float)textureMapHeight);
    glVertex2f(0, 1);

    glEnd();
    glDisable(GL_TEXTURE_2D);
  }

  void drawTextureMapAsPoints() {
    float ratioX = (float)resolutionX/(float)textureMapWidth;
    float ratioY = (float)resolutionY/(float)textureMapHeight;

    glPointSize(1.0);
    glBegin(GL_POINTS);

    openni::RGB888Pixel* textureMapRow = textureMap;
    float vx, vy;
    for(unsigned int y = 0; y < textureMapHeight; y++) {
      openni::RGB888Pixel* pTex = textureMapRow;
      vy = (float) y / textureMapHeight / ratioY;
      for(unsigned int x = 0; x < textureMapWidth; x++) {
	glColor4f((float)pTex->r / 255,
		  (float)pTex->g / 255,
		  (float)pTex->b / 255,
		  1);
	vx = (float) x / textureMapWidth / ratioX;
	glVertex2f(vx, vy);
	pTex++;
      }
      textureMapRow += textureMapWidth;
    }

    glEnd();
  }

  int resolutionX, resolutionY;
  bool depthAsPoints;
  openni::RGB888Pixel* textureMap;
  unsigned int textureMapWidth;
  unsigned int textureMapHeight;
};
