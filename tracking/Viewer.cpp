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

bool g_drawSkeleton = true;
bool g_drawCenterOfMass = false;
bool g_drawStatusLabel = true;
bool g_drawBoundingBox = false;
bool g_drawBackground = true;
bool g_drawDepth = true;
bool g_drawFrameId = false;
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

float Colors[][3] = {{1, 0, 0}, {0, 1, 0}, {0, 0, 1}, {1, 1, 1}};
int colorCount = 3;

#define MAX_USERS 10
bool g_visibleUsers[MAX_USERS] = {false};
nite::SkeletonState g_skeletonStates[MAX_USERS] = {nite::SKELETON_NONE};
char g_userStatusLabels[MAX_USERS][100] = {{0}};

char g_generalMessage[100] = {0};

#define USER_MESSAGE(msg) {\
	sprintf(g_userStatusLabels[user.getId()], "%s", msg);\
	printf("[%08" PRIu64 "] User #%d:\t%s\n", ts, user.getId(), msg);}

void Viewer::updateUserState(const nite::UserData& user, uint64_t ts)
{
	if (user.isNew())
	{
		USER_MESSAGE("New");
	}
	else if (user.isVisible() && !g_visibleUsers[user.getId()])
		printf("[%08" PRIu64 "] User #%d:\tVisible\n", ts, user.getId());
	else if (!user.isVisible() && g_visibleUsers[user.getId()])
		printf("[%08" PRIu64 "] User #%d:\tOut of Scene\n", ts, user.getId());
	else if (user.isLost())
	{
		USER_MESSAGE("Lost");
	}
	g_visibleUsers[user.getId()] = user.isVisible();


	if(g_skeletonStates[user.getId()] != user.getSkeleton().getState())
	{
		switch(g_skeletonStates[user.getId()] = user.getSkeleton().getState())
		{
		case nite::SKELETON_NONE:
			USER_MESSAGE("Stopped tracking.")
			break;
		case nite::SKELETON_CALIBRATING:
			USER_MESSAGE("Calibrating...")
			break;
		case nite::SKELETON_TRACKED:
			USER_MESSAGE("Tracking!")
			break;
		case nite::SKELETON_CALIBRATION_ERROR_NOT_IN_POSE:
		case nite::SKELETON_CALIBRATION_ERROR_HANDS:
		case nite::SKELETON_CALIBRATION_ERROR_LEGS:
		case nite::SKELETON_CALIBRATION_ERROR_HEAD:
		case nite::SKELETON_CALIBRATION_ERROR_TORSO:
			USER_MESSAGE("Calibration Failed... :-|")
			break;
		}
	}
}

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
  m_pUserTracker = getUserTracker();
  userTrackerFrame = getUserTrackerFrame();

	log("getDepthFrame\n");
	depthFrame = userTrackerFrame.getDepthFrame();

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

	log("getUsers\n");
	const nite::Array<nite::UserData>& users = userTrackerFrame.getUsers();

	log("draw users\n");
	for (int i = 0; i < users.getSize(); ++i)
	{
		const nite::UserData& user = users[i];

		updateUserState(user, userTrackerFrame.getTimestamp());
		if (user.isNew())
		{
		}
		else if (!user.isLost())
		{
			if (g_drawStatusLabel)
			{
				DrawStatusLabel(user);
			}
			if (g_drawCenterOfMass)
			{
				DrawCenterOfMass(user);
			}
			if (g_drawBoundingBox)
			{
				DrawBoundingBox(user);
			}

			if (user.getSkeleton().getState() == nite::SKELETON_TRACKED && g_drawSkeleton)
			{
				DrawSkeleton(user);
			}
		}
	}

	if (g_drawFrameId)
	{
		DrawFrameId(userTrackerFrame.getFrameIndex());
	}

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

  float factor[3] = {1, 1, 1};
  // check if we need to draw depth frame to texture
  if (depthFrame.isValid() && g_drawDepth)
    {
      log("getUserMap\n");
      const nite::UserMap& userLabels = userTrackerFrame.getUserMap();

      log("draw frame to texture\n");
      const nite::UserId* pLabels = userLabels.getPixels();

      const openni::DepthPixel* pDepthRow = (const openni::DepthPixel*)depthFrame.getData();
      openni::RGB888Pixel* pTexRow = m_pTexMap + depthFrame.getCropOriginY() * m_nTexMapX;
      int rowSize = depthFrame.getStrideInBytes() / sizeof(openni::DepthPixel);

      log("rowSize=%d height=%d width=%d\n", rowSize, depthFrame.getHeight(), depthFrame.getWidth());
      for (int y = 0; y < depthFrame.getHeight(); ++y)
	{
	  const openni::DepthPixel* pDepth = pDepthRow;
	  openni::RGB888Pixel* pTex = pTexRow + depthFrame.getCropOriginX();

	  for (int x = 0; x < depthFrame.getWidth(); ++x, ++pDepth, ++pTex, ++pLabels)
	    {
	      if (*pDepth != 0)
		{
		  if (*pLabels == 0)
		    {
		      if (!g_drawBackground)
			{
			  factor[0] = factor[1] = factor[2] = 0;

			}
		      else
			{
			  factor[0] = Colors[colorCount][0];
			  factor[1] = Colors[colorCount][1];
			  factor[2] = Colors[colorCount][2];
			}
		    }
		  else
		    {
		      factor[0] = Colors[*pLabels % colorCount][0];
		      factor[1] = Colors[*pLabels % colorCount][1];
		      factor[2] = Colors[*pLabels % colorCount][2];
		    }
		  //					// Add debug lines - every 10cm
		  // 					else if ((*pDepth / 10) % 10 == 0)
		  // 					{
		  // 						factor[0] = factor[2] = 0;
		  // 					}

		  int nHistValue = m_pDepthHist[*pDepth];
		  pTex->r = nHistValue*factor[0];
		  pTex->g = nHistValue*factor[1];
		  pTex->b = nHistValue*factor[2];

		  factor[0] = factor[1] = factor[2] = 1;
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
	case 's':
		// Draw skeleton?
		g_drawSkeleton = !g_drawSkeleton;
		break;
	case 'l':
		// Draw user status label?
		g_drawStatusLabel = !g_drawStatusLabel;
		break;
	case 'c':
		// Draw center of mass?
		g_drawCenterOfMass = !g_drawCenterOfMass;
		break;
	case 'x':
		// Draw bounding box?
		g_drawBoundingBox = !g_drawBoundingBox;
		break;
	case 'b':
		// Draw background?
		g_drawBackground = !g_drawBackground;
		break;
	case 'd':
		// Draw depth?
		g_drawDepth = !g_drawDepth;
		break;
	case 'f':
		// Draw frame ID
		g_drawFrameId = !g_drawFrameId;
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

void Viewer::DrawStatusLabel(const nite::UserData& user)
{
	int color = user.getId() % colorCount;
	glColor3f(1.0f - Colors[color][0], 1.0f - Colors[color][1], 1.0f - Colors[color][2]);

	float x,y;
	m_pUserTracker->convertJointCoordinatesToDepth(user.getCenterOfMass().x, user.getCenterOfMass().y, user.getCenterOfMass().z, &x, &y);
	x /= (float)g_nXRes;
	y /= (float)g_nYRes;
	char *msg = g_userStatusLabels[user.getId()];
	glRasterPos2f(x - float((strlen(msg)/2)*8)/g_nXRes, y);
	glPrintString(GLUT_BITMAP_HELVETICA_18, msg);
	checkGlErrors();
}

void Viewer::DrawCenterOfMass(const nite::UserData& user)
{
	glColor3f(1.0f, 1.0f, 1.0f);

	float coordinates[3] = {0};

	m_pUserTracker->convertJointCoordinatesToDepth(user.getCenterOfMass().x, user.getCenterOfMass().y, user.getCenterOfMass().z, &coordinates[0], &coordinates[1]);

	coordinates[0] /= (float)g_nXRes;
	coordinates[1] /= (float)g_nYRes;
	glPointSize(8);
	glVertexPointer(3, GL_FLOAT, 0, coordinates);
	glDrawArrays(GL_POINTS, 0, 1);
	checkGlErrors();

}

void Viewer::DrawBoundingBox(const nite::UserData& user)
{
	glColor3f(1.0f, 1.0f, 1.0f);

	float coordinates[] =
	{
		user.getBoundingBox().max.x, user.getBoundingBox().max.y, 0,
		user.getBoundingBox().max.x, user.getBoundingBox().min.y, 0,
		user.getBoundingBox().min.x, user.getBoundingBox().min.y, 0,
		user.getBoundingBox().min.x, user.getBoundingBox().max.y, 0,
	};
	coordinates[0]  /= (float)g_nXRes;
	coordinates[1]  /= (float)g_nYRes;
	coordinates[3]  /= (float)g_nXRes;
	coordinates[4]  /= (float)g_nYRes;
	coordinates[6]  /= (float)g_nXRes;
	coordinates[7]  /= (float)g_nYRes;
	coordinates[9]  /= (float)g_nXRes;
	coordinates[10] /= (float)g_nYRes;

	glPointSize(2);
	glVertexPointer(3, GL_FLOAT, 0, coordinates);
	glDrawArrays(GL_LINE_LOOP, 0, 4);
	checkGlErrors();

}

void Viewer::DrawLimb(const nite::SkeletonJoint& joint1, const nite::SkeletonJoint& joint2, int color)
{
	float coordinates[6] = {0};
	m_pUserTracker->convertJointCoordinatesToDepth(joint1.getPosition().x, joint1.getPosition().y, joint1.getPosition().z, &coordinates[0], &coordinates[1]);
	m_pUserTracker->convertJointCoordinatesToDepth(joint2.getPosition().x, joint2.getPosition().y, joint2.getPosition().z, &coordinates[3], &coordinates[4]);

	coordinates[0] /= (float)g_nXRes;
	coordinates[1] /= (float)g_nYRes;
	coordinates[3] /= (float)g_nXRes;
	coordinates[4] /= (float)g_nYRes;

	if (joint1.getPositionConfidence() == 1 && joint2.getPositionConfidence() == 1)
	{
		glColor3f(1.0f - Colors[color][0], 1.0f - Colors[color][1], 1.0f - Colors[color][2]);
	}
	else if (joint1.getPositionConfidence() < 0.5f || joint2.getPositionConfidence() < 0.5f)
	{
		return;
	}
	else
	{
		glColor3f(.5, .5, .5);
	}
	glPointSize(2);
	glVertexPointer(3, GL_FLOAT, 0, coordinates);
	glDrawArrays(GL_LINES, 0, 2);

	glPointSize(10);
	if (joint1.getPositionConfidence() == 1)
	{
		glColor3f(1.0f - Colors[color][0], 1.0f - Colors[color][1], 1.0f - Colors[color][2]);
	}
	else
	{
		glColor3f(.5, .5, .5);
	}
	glVertexPointer(3, GL_FLOAT, 0, coordinates);
	glDrawArrays(GL_POINTS, 0, 1);

	if (joint2.getPositionConfidence() == 1)
	{
		glColor3f(1.0f - Colors[color][0], 1.0f - Colors[color][1], 1.0f - Colors[color][2]);
	}
	else
	{
		glColor3f(.5, .5, .5);
	}
	glVertexPointer(3, GL_FLOAT, 0, coordinates+3);
	glDrawArrays(GL_POINTS, 0, 1);
	checkGlErrors();
}

void Viewer::DrawSkeleton(const nite::UserData& userData)
{
	DrawLimb(userData.getSkeleton().getJoint(nite::JOINT_HEAD), userData.getSkeleton().getJoint(nite::JOINT_NECK), userData.getId() % colorCount);

	DrawLimb(userData.getSkeleton().getJoint(nite::JOINT_LEFT_SHOULDER), userData.getSkeleton().getJoint(nite::JOINT_LEFT_ELBOW), userData.getId() % colorCount);
	DrawLimb(userData.getSkeleton().getJoint(nite::JOINT_LEFT_ELBOW), userData.getSkeleton().getJoint(nite::JOINT_LEFT_HAND), userData.getId() % colorCount);

	DrawLimb(userData.getSkeleton().getJoint(nite::JOINT_RIGHT_SHOULDER), userData.getSkeleton().getJoint(nite::JOINT_RIGHT_ELBOW), userData.getId() % colorCount);
	DrawLimb(userData.getSkeleton().getJoint(nite::JOINT_RIGHT_ELBOW), userData.getSkeleton().getJoint(nite::JOINT_RIGHT_HAND), userData.getId() % colorCount);

	DrawLimb(userData.getSkeleton().getJoint(nite::JOINT_LEFT_SHOULDER), userData.getSkeleton().getJoint(nite::JOINT_RIGHT_SHOULDER), userData.getId() % colorCount);

	DrawLimb(userData.getSkeleton().getJoint(nite::JOINT_LEFT_SHOULDER), userData.getSkeleton().getJoint(nite::JOINT_TORSO), userData.getId() % colorCount);
	DrawLimb(userData.getSkeleton().getJoint(nite::JOINT_RIGHT_SHOULDER), userData.getSkeleton().getJoint(nite::JOINT_TORSO), userData.getId() % colorCount);

	DrawLimb(userData.getSkeleton().getJoint(nite::JOINT_TORSO), userData.getSkeleton().getJoint(nite::JOINT_LEFT_HIP), userData.getId() % colorCount);
	DrawLimb(userData.getSkeleton().getJoint(nite::JOINT_TORSO), userData.getSkeleton().getJoint(nite::JOINT_RIGHT_HIP), userData.getId() % colorCount);

	DrawLimb(userData.getSkeleton().getJoint(nite::JOINT_LEFT_HIP), userData.getSkeleton().getJoint(nite::JOINT_RIGHT_HIP), userData.getId() % colorCount);


	DrawLimb(userData.getSkeleton().getJoint(nite::JOINT_LEFT_HIP), userData.getSkeleton().getJoint(nite::JOINT_LEFT_KNEE), userData.getId() % colorCount);
	DrawLimb(userData.getSkeleton().getJoint(nite::JOINT_LEFT_KNEE), userData.getSkeleton().getJoint(nite::JOINT_LEFT_FOOT), userData.getId() % colorCount);

	DrawLimb(userData.getSkeleton().getJoint(nite::JOINT_RIGHT_HIP), userData.getSkeleton().getJoint(nite::JOINT_RIGHT_KNEE), userData.getId() % colorCount);
	DrawLimb(userData.getSkeleton().getJoint(nite::JOINT_RIGHT_KNEE), userData.getSkeleton().getJoint(nite::JOINT_RIGHT_FOOT), userData.getId() % colorCount);
	checkGlErrors();
}
