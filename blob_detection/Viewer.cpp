#if (defined _WIN32)
#define PRIu64 "llu"
#else
#define __STDC_FORMAT_MACROS
#include <inttypes.h>
#endif

#include "Viewer.hpp"
#include <sys/time.h>
#include <stdarg.h>

#if (ONI_PLATFORM == ONI_PLATFORM_MACOSX)
        #include <GLUT/glut.h>
#else
        #include <GL/glut.h>
#endif

#define GL_WIN_SIZE_X	640
#define GL_WIN_SIZE_Y	480
#define TEXTURE_SIZE	512

#define DEFAULT_DISPLAY_MODE	DISPLAY_MODE_DEPTH

#define MIN_NUM_CHUNKS(data_size, chunk_size)	((((data_size)-1) / (chunk_size) + 1))
#define MIN_CHUNKS_SIZE(data_size, chunk_size)	(MIN_NUM_CHUNKS(data_size, chunk_size) * (chunk_size))

Viewer* Viewer::ms_self = NULL;

bool g_drawDepth = true;
bool verbose = false;

int g_nXRes = 0, g_nYRes = 0;

void log(const char *format, ...) {
  va_list args;
  if(verbose) {
    va_start(args, format);
    vfprintf(stdout, format, args);
    va_end(args);
    fflush(stdout);
  }
}

#define checkGlErrors() _checkGlErrors(__LINE__)

int _checkGlErrors(int line) {
  GLenum err;
  int numErrors = 0;
  while ((err = glGetError()) != GL_NO_ERROR) {
    printf("OpenGL error at line %d: %s\n", line, gluErrorString(err));
    numErrors++;
  }
  return numErrors;
}

// time to hold in pose to exit program. In milliseconds.
const int g_poseTimeoutToExit = 2000;

void calculateHistogram(float* pHistogram, int histogramSize, const openni::VideoFrameRef& depthFrame)
{
	const openni::DepthPixel* pDepth = (const openni::DepthPixel*)depthFrame.getData();
	int width = depthFrame.getWidth();
	int height = depthFrame.getHeight();
	// Calculate the accumulative histogram (the yellow display...)
	memset(pHistogram, 0, histogramSize*sizeof(float));
	int restOfRow = depthFrame.getStrideInBytes() / sizeof(openni::DepthPixel) - width;

	unsigned int nNumberOfPoints = 0;
	for (int y = 0; y < height; ++y)
	{
		for (int x = 0; x < width; ++x, ++pDepth)
		{
			if (*pDepth != 0)
			{
				pHistogram[*pDepth]++;
				nNumberOfPoints++;
			}
		}
		pDepth += restOfRow;
	}
	for (int nIndex=1; nIndex<histogramSize; nIndex++)
	{
		pHistogram[nIndex] += pHistogram[nIndex-1];
	}
	if (nNumberOfPoints)
	{
		for (int nIndex=1; nIndex<histogramSize; nIndex++)
		{
			pHistogram[nIndex] = (256 * (1.0f - (pHistogram[nIndex] / nNumberOfPoints)));
		}
	}
}

void Viewer::glutIdle()
{
  log("glutIdle\n");
	glutPostRedisplay();
}

void Viewer::glutReshape(int width, int height) {
  Viewer::ms_self->ResizedWindow(width, height);
}

void Viewer::glutDisplay()
{
  log("glutDisplay\n");
	Viewer::ms_self->Display();
}
void Viewer::glutKeyboard(unsigned char key, int x, int y)
{
	Viewer::ms_self->OnKey(key, x, y);
}

Viewer::Viewer()
{
	ms_self = this;
}
Viewer::~Viewer()
{
	delete[] m_pTexMap;
	ms_self = NULL;
}

openni::Status Viewer::Init(int argc, char **argv)
{
	m_pTexMap = NULL;
	return InitOpenGL(argc, argv);
}

openni::Status Viewer::Run()	//Does not return
{
  previousDisplayTime = 0;
	glutMainLoop();

	return openni::STATUS_OK;
}

char g_generalMessage[100] = {0};

#define USER_MESSAGE(msg) {\
	sprintf(g_userStatusLabels[user.getId()], "%s", msg);\
	printf("[%08" PRIu64 "] User #%d:\t%s\n", ts, user.getId(), msg);}

#ifndef USE_GLES
void glPrintString(void *font, const char *str)
{
	int i,l = (int)strlen(str);

	for(i=0; i<l; i++)
	{   
		glutBitmapCharacter(font,*str++);
	}   
	checkGlErrors();
}
#endif
void DrawFrameId(int frameId)
{
	char buffer[80] = "";
	sprintf(buffer, "%d", frameId);
	glColor3f(1.0f, 0.0f, 0.0f);
	glRasterPos2f(20.0/GL_WIN_SIZE_X, 20.0/GL_WIN_SIZE_Y);
	glPrintString(GLUT_BITMAP_HELVETICA_18, buffer);
	checkGlErrors();
}

void Viewer::ResizedWindow(int width, int height)
{
  windowWidth = width;
  windowHeight = height;
  glViewport(0, 0, windowWidth, windowHeight);
}

void Viewer::Display()
{
  struct timeval tv;
  uint64_t currentDisplayTime, timeDiff;
  gettimeofday(&tv, NULL);
  currentDisplayTime = (uint64_t) (tv.tv_sec * 1000000 + tv.tv_usec);
  if(previousDisplayTime != 0) {
    timeDiff = currentDisplayTime - previousDisplayTime;
    log("time diff: %ld\n", timeDiff);
  }
  previousDisplayTime = currentDisplayTime;

  processFrame();

	depthFrame = getDepthFrame();

	if (m_pTexMap == NULL)
	{
		// Texture map init
		m_nTexMapX = MIN_CHUNKS_SIZE(depthFrame.getVideoMode().getResolutionX(), TEXTURE_SIZE);
		m_nTexMapY = MIN_CHUNKS_SIZE(depthFrame.getVideoMode().getResolutionY(), TEXTURE_SIZE);
		m_pTexMap = new openni::RGB888Pixel[m_nTexMapX * m_nTexMapY];
	}

	glClear (GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT);

	glMatrixMode(GL_PROJECTION);
	glLoadIdentity();
	glOrtho(0, 1.0, 1.0, 0, -1.0, 1.0);
        glMatrixMode(GL_MODELVIEW);
	glPushMatrix();
	checkGlErrors();

	if (depthFrame.isValid() && g_drawDepth)
	{
	  log("calculateHistogram\n");
	  calculateHistogram(m_pDepthHist, MAX_DEPTH, depthFrame);
	}

	updateTextureMap();
	g_nXRes = depthFrame.getVideoMode().getResolutionX();
	g_nYRes = depthFrame.getVideoMode().getResolutionY();
	drawTextureMap();

	if (g_generalMessage[0] != '\0')
	{
		char *msg = g_generalMessage;
		glColor3f(1.0f, 0.0f, 0.0f);
		glRasterPos2f(100.0/GL_WIN_SIZE_X, 20.0/GL_WIN_SIZE_Y);
		glPrintString(GLUT_BITMAP_HELVETICA_18, msg);
	}


	glPopMatrix();
	// Swap the OpenGL display buffers
	glutSwapBuffers();

	checkGlErrors();
	log("Display done\n");
}

void Viewer::updateTextureMap() {
  memset(m_pTexMap, 0, m_nTexMapX*m_nTexMapY*sizeof(openni::RGB888Pixel));

  // check if we need to draw depth frame to texture
  if (depthFrame.isValid() && g_drawDepth)
    {
      const openni::DepthPixel* pDepthRow = (const openni::DepthPixel*)depthFrame.getData();
      openni::RGB888Pixel* pTexRow = m_pTexMap + depthFrame.getCropOriginY() * m_nTexMapX;
      int rowSize = depthFrame.getStrideInBytes() / sizeof(openni::DepthPixel);

      log("rowSize=%d height=%d width=%d\n", rowSize, depthFrame.getHeight(), depthFrame.getWidth());
      for (int y = 0; y < depthFrame.getHeight(); ++y)
	{
	  const openni::DepthPixel* pDepth = pDepthRow;
	  openni::RGB888Pixel* pTex = pTexRow + depthFrame.getCropOriginX();

	  for (int x = 0; x < depthFrame.getWidth(); ++x, ++pDepth, ++pTex)
	    {
	      if (*pDepth != 0)
		{
		  int nHistValue = m_pDepthHist[*pDepth];
		  pTex->r = nHistValue;
		  pTex->g = nHistValue;
		  pTex->b = nHistValue;
		}
	    }

	  pDepthRow += rowSize;
	  pTexRow += m_nTexMapX;
	}
      log("drew frame to texture\n");
    }
}

void Viewer::drawTextureMap() {
  if(depthAsPoints)
    drawTextureMapAsPoints();
  else
    drawTextureMapAsTexture();
}

void Viewer::drawTextureMapAsTexture() {
  glTexParameteri(GL_TEXTURE_2D, GL_GENERATE_MIPMAP_SGIS, GL_TRUE);
  checkGlErrors();
  glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR_MIPMAP_LINEAR);
  checkGlErrors();
  glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR);
  checkGlErrors();
  log("glTexImage2D\n");
  glTexImage2D(GL_TEXTURE_2D, 0, GL_RGB, m_nTexMapX, m_nTexMapY, 0, GL_RGB, GL_UNSIGNED_BYTE, m_pTexMap);
  checkGlErrors();
  log("glTexImage2D ok\n");

  // Display the OpenGL texture map
  glColor4f(1,1,1,1);

  glEnable(GL_TEXTURE_2D);
  checkGlErrors();
  glBegin(GL_QUADS);

  // upper left
  glTexCoord2f(0, 0);
  glVertex2f(0, 0);
  // upper right
  glTexCoord2f((float)g_nXRes/(float)m_nTexMapX, 0);
  glVertex2f(1, 0);
  // bottom right
  glTexCoord2f((float)g_nXRes/(float)m_nTexMapX, (float)g_nYRes/(float)m_nTexMapY);
  glVertex2f(1, 1);
  // bottom left
  glTexCoord2f(0, (float)g_nYRes/(float)m_nTexMapY);
  glVertex2f(0, 1);

  glEnd();
  glDisable(GL_TEXTURE_2D);
  checkGlErrors();
}

void Viewer::drawTextureMapAsPoints() {
  float ratioX = (float)g_nXRes/(float)m_nTexMapX;
  float ratioY = (float)g_nYRes/(float)m_nTexMapY;

  glPointSize(1.0);
  glBegin(GL_POINTS);

  openni::RGB888Pixel* pTexRow = m_pTexMap;
  float vx, vy;
  for(unsigned int y = 0; y < m_nTexMapY; y++) {
    openni::RGB888Pixel* pTex = pTexRow;
    vy = (float) y / m_nTexMapY / ratioY;
    for(unsigned int x = 0; x < m_nTexMapX; x++) {
      glColor4f((float)pTex->r / 255,
      		(float)pTex->g / 255,
      		(float)pTex->b / 255,
      		1);
      vx = (float) x / m_nTexMapX / ratioX;
      glVertex2f(vx, vy);
      pTex++;
    }
    pTexRow += m_nTexMapX;
  }

  glEnd();
  checkGlErrors();
}

void Viewer::OnKey(unsigned char key, int /*x*/, int /*y*/)
{
	switch (key)
	{
	case 27:
		exit (1);
	case 'd':
		// Draw depth?
		g_drawDepth = !g_drawDepth;
		break;
	}

}

openni::Status Viewer::InitOpenGL(int argc, char **argv)
{
	glutInit(&argc, argv);
	glutInitDisplayMode(GLUT_RGB | GLUT_DOUBLE | GLUT_DEPTH);
	glutInitWindowSize(GL_WIN_SIZE_X, GL_WIN_SIZE_Y);
	glutCreateWindow ("Tracker");
	// 	glutFullScreen();
	glutSetCursor(GLUT_CURSOR_NONE);

	InitOpenGLHooks();

	glDisable(GL_DEPTH_TEST);
	glEnable(GL_TEXTURE_2D);

	glEnableClientState(GL_VERTEX_ARRAY);
	glDisableClientState(GL_COLOR_ARRAY);

	return openni::STATUS_OK;

}

void Viewer::InitOpenGLHooks()
{
	glutKeyboardFunc(glutKeyboard);
	glutDisplayFunc(glutDisplay);
	glutIdleFunc(glutIdle);
	glutReshapeFunc(glutReshape);
}
