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
  virtual void DisplayPostDraw(){};
  void DrawStatusLabel(const nite::UserData& user);
  void DrawCenterOfMass(const nite::UserData& user);
  void DrawBoundingBox(const nite::UserData& user);
  void DrawLimb(const nite::SkeletonJoint& joint1, const nite::SkeletonJoint& joint2, int color);
  void DrawSkeleton(const nite::UserData& userData);


  virtual void OnKey(unsigned char key, int x, int y);

  virtual openni::Status InitOpenGL(int argc, char **argv);
  void InitOpenGLHooks();

  virtual void processFrame() = 0;
  virtual nite::UserTracker *getUserTracker() = 0;
  virtual nite::UserTrackerFrameRef getUserTrackerFrame() = 0;

private:
  Viewer(const Viewer&);
  Viewer& operator=(Viewer&);

  static Viewer* ms_self;
  static void glutIdle();
  static void glutReshape(int width, int height);
  static void glutDisplay();
  static void glutKeyboard(unsigned char key, int x, int y);
  void updateUserState(const nite::UserData& user, uint64_t ts);
  void updateTextureMap();
  void drawTextureMap();
  void drawTextureMapAsTexture();
  void drawTextureMapAsPoints();

  nite::UserTracker* m_pUserTracker;
  nite::UserTrackerFrameRef userTrackerFrame;
  openni::VideoFrameRef depthFrame;
  float	m_pDepthHist[MAX_DEPTH];
  openni::RGB888Pixel* m_pTexMap;
  unsigned int m_nTexMapX;
  unsigned int m_nTexMapY;

  uint64_t previousDisplayTime;
  int windowWidth, windowHeight;
};


#endif
