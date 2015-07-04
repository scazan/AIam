/*******************************************************************************
*                                                                              *
*   PrimeSense NiTE 2.0 - User Viewer Sample                                   *
*   Copyright (C) 2012 PrimeSense Ltd.                                         *
*                                                                              *
*******************************************************************************/

#ifndef _NITE_USER_VIEWER_H_
#define _NITE_USER_VIEWER_H_

#include "NiTE.h"

#define MAX_DEPTH 10000

class SampleViewer
{
public:
	SampleViewer(const char* strSampleName);
	virtual ~SampleViewer();

	virtual openni::Status Init(int argc, char **argv);
	virtual openni::Status Run();	//Does not return

protected:
	virtual void Display();
	void ResizedWindow(int width, int height);
	virtual void DisplayPostDraw(){};	// Overload to draw over the screen image
	void DrawStatusLabel(const nite::UserData& user);
	void DrawCenterOfMass(const nite::UserData& user);
	void DrawBoundingBox(const nite::UserData& user);
	void DrawLimb(const nite::SkeletonJoint& joint1, const nite::SkeletonJoint& joint2, int color);
	void DrawSkeleton(const nite::UserData& userData);


	virtual void OnKey(unsigned char key, int x, int y);

	virtual openni::Status InitOpenGL(int argc, char **argv);
	void InitOpenGLHooks();

	void Finalize();

private:
	SampleViewer(const SampleViewer&);
	SampleViewer& operator=(SampleViewer&);

	static SampleViewer* ms_self;
	static void glutIdle();
	static void glutReshape(int width, int height);
	static void glutDisplay();
	static void glutKeyboard(unsigned char key, int x, int y);

	float				m_pDepthHist[MAX_DEPTH];
	char			m_strSampleName[ONI_MAX_STR];
	openni::RGB888Pixel*		m_pTexMap;
	unsigned int		m_nTexMapX;
	unsigned int		m_nTexMapY;

	openni::Device		m_device;
	openni::Recorder recorder;
	const char* recordingFilename;
	openni::VideoStream depthStream;
	nite::UserTracker* m_pUserTracker;

	nite::UserId m_poseUser;
	uint64_t m_poseTime;
	uint64_t previousDisplayTime;
	int windowWidth, windowHeight;
};


#endif // _NITE_USER_VIEWER_H_
