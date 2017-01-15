#ifndef _VIEWER_H_
#define _VIEWER_H_

#include "NiTE.h"

#define MAX_DEPTH 10000

class Viewer
{
public:
  Viewer();
  virtual ~Viewer();

  virtual openni::Status Init(int argc, char **argv);
  virtual openni::Status Run();

  bool depthAsPoints;

protected:
  virtual void Display();
  void ResizedWindow(int width, int height);

  virtual void OnKey(unsigned char key, int x, int y);

  virtual openni::Status InitOpenGL(int argc, char **argv);
  void InitOpenGLHooks();

  virtual void processFrame() = 0;
  virtual openni::VideoFrameRef getDepthFrame() = 0;

private:
  Viewer(const Viewer&);
  Viewer& operator=(Viewer&);

  static Viewer* ms_self;
  static void glutIdle();
  static void glutReshape(int width, int height);
  static void glutDisplay();
  static void glutKeyboard(unsigned char key, int x, int y);
  void updateTextureMap();
  void drawTextureMap();
  void drawTextureMapAsTexture();
  void drawTextureMapAsPoints();

  openni::VideoFrameRef depthFrame;
  float	m_pDepthHist[MAX_DEPTH];
  openni::RGB888Pixel* m_pTexMap;
  unsigned int m_nTexMapX;
  unsigned int m_nTexMapY;

  uint64_t previousDisplayTime;
  int windowWidth, windowHeight;
};


#endif
