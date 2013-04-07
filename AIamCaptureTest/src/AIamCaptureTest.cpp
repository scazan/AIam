/*
 Copyright (C) 2013 Gabor Papp

 This program is free software; you can redistribute it and/or modify
 it under the terms of the GNU General Public License as published by
 the Free Software Foundation; either version 3 of the License, or
 (at your option) any later version.

 This program is distributed in the hope that it will be useful,
 but WITHOUT ANY WARRANTY; without even the implied warranty of
 MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 GNU General Public License for more details.

 You should have received a copy of the GNU General Public License
 along with this program. If not, see <http://www.gnu.org/licenses/>.
*/

#include <vector>

#include "cinder/Cinder.h"
#include "cinder/app/AppBasic.h"
#include "cinder/gl/gl.h"
#include "cinder/params/Params.h"
#include "cinder/Camera.h"
#include "cinder/MayaCamUI.h"

#include "AssimpLoader.h"

using namespace ci;
using namespace ci::app;
using namespace std;
using namespace mndl;

class AIamCaptureTest : public AppBasic
{
	public:
		void prepareSettings( Settings *settings );
		void setup();

		void keyDown( KeyEvent event );
		void mouseDown( MouseEvent event );
		void mouseDrag( MouseEvent event );
		void resize();

		void update();
		void draw();

	private:
		params::InterfaceGl mParams;

		float mFps;
		bool mVerticalSyncEnabled = false;

		typedef shared_ptr< assimp::AssimpLoader > AssimpLoaderRef;
		vector< AssimpLoaderRef > mMotions;
		int mMotionIndex;

		MayaCamUI mMayaCam;

		//! Returns paths of bvh files in the directory.
		vector< fs::path > getBvhs( const fs::path & relativeDir );
		vector< fs::path > mBvhPaths; //< all bvh paths
		//! Loads some bvh files.
		void loadSomeBvhs();
		bool mAllBvhsLoaded = false;
		float mLoadingProgress;
		vector< string > mMotionNames;
};

void AIamCaptureTest::prepareSettings( Settings *settings )
{
	settings->setWindowSize( 800, 600 );
}

void AIamCaptureTest::setup()
{
	mParams = params::InterfaceGl( "Parameters", Vec2i( 200, 300 ) );
	mParams.addParam( "Fps", &mFps, "", true );
	mParams.addParam( "Vertical sync", &mVerticalSyncEnabled );
	mParams.addSeparator();

	CameraPersp cam;
	cam.setPerspective( 60, getWindowAspectRatio(), 0.1f, 1000.0f );
	cam.setEyePoint( Vec3f( 0, 30, 200 ) );
	cam.setCenterOfInterestPoint( Vec3f( 0, 70, 0 ) );
	mMayaCam.setCurrentCam( cam );

	mMotions.push_back( AssimpLoaderRef() );
	mMotionNames.push_back( "no motion" );
	mBvhPaths = getBvhs( "motions" );
}


vector< fs::path > AIamCaptureTest::getBvhs( const fs::path &relativeDir )
{
	vector< fs::path > files;

	fs::path dataPath = app::getAssetPath( relativeDir );

	for ( fs::directory_iterator it( dataPath ); it != fs::directory_iterator(); ++it )
	{
		if ( fs::is_regular_file( *it ) && ( it->path().extension().string() == ".bvh" ) )
		{
			files.push_back( relativeDir / it->path().filename() );
		}
	}

	return files;
}

void AIamCaptureTest::loadSomeBvhs()
{
	const int loadNum = 5;
	static size_t bvhNum = mBvhPaths.size();
	int i = 0;

	auto bIt = mBvhPaths.begin();
	while ( ( bIt != mBvhPaths.end() ) && ( i < loadNum ) )
	{
		AssimpLoaderRef aref( AssimpLoaderRef( new assimp::AssimpLoader( getAssetPath( *bIt ) ) ) );
		aref->setAnimation( 0 );
		aref->enableSkinning( true );
		aref->enableAnimation( true );
		mMotions.push_back( aref );
		mMotionNames.push_back( bIt->filename().string() );

		++i;
		bIt = mBvhPaths.erase( bIt );
	}

	if ( ( mLoadingProgress > .999f ) && mBvhPaths.empty() )
	{
		mAllBvhsLoaded = true;
		mMotionIndex = 0;
		mParams.addParam( "Motions", mMotionNames, &mMotionIndex );
	}

	if ( bvhNum )
		mLoadingProgress = (float)( mMotions.size() )/ (float)bvhNum;
	else
		mLoadingProgress = 1.f;

}

void AIamCaptureTest::update()
{
	mFps = getAverageFps();

	if ( mVerticalSyncEnabled != gl::isVerticalSyncEnabled() )
		gl::enableVerticalSync( mVerticalSyncEnabled );

	if ( !mAllBvhsLoaded )
	{
		loadSomeBvhs();
		return;
	}

	static int lastMotionIndex = -1;
	static double lastStartTime;

	if ( mMotions[ mMotionIndex ] )
	{
		if ( mMotionIndex != lastMotionIndex ) // change motion
		{
			lastStartTime = getElapsedSeconds();
			lastMotionIndex = mMotionIndex;
		}

		double motionDuration = mMotions[ mMotionIndex ]->getAnimationDuration( 0 );
		double currentMotionTime = math< double >::clamp( getElapsedSeconds() - lastStartTime, 0., motionDuration );
		mMotions[ mMotionIndex ]->setTime( currentMotionTime );
		mMotions[ mMotionIndex ]->update();
	}
}

void AIamCaptureTest::draw()
{
	gl::clear( Color::white() );

	gl::setViewport( getWindowBounds() );
	if ( !mAllBvhsLoaded )
	{
		gl::disableDepthRead();
		gl::enableAlphaBlending();
		gl::setMatricesWindow( getWindowSize() );
		float w = getWindowWidth();
		float h = getWindowHeight();
		float h2 = h / 2.f;
		float s = h / 50.f;
		Rectf progressbar( Vec2f( 0.f, h2 - s ), Vec2f( mLoadingProgress * w, h2 + s ) );
		gl::drawSolidRect( progressbar );
		Font font( Font::getDefault().getName(), s );
		gl::drawString( "Loading motions...", Vec2f( 5.f, h2 - 2 * s ), ColorA::black(), font );
		gl::color( Color::black() );
		gl::disableAlphaBlending();
	}
	else
	{
		gl::setMatrices( mMayaCam.getCamera() );

		gl::enableDepthWrite();
		gl::enableDepthRead();

		gl::color( Color::white() );
		gl::drawCoordinateFrame( 10.f, 2.f, 0.5f );

		if ( mMotions[ mMotionIndex ] )
			mMotions[ mMotionIndex ]->draw();
	}

	params::InterfaceGl::draw();
}

void AIamCaptureTest::mouseDown( MouseEvent event )
{
	mMayaCam.mouseDown( event.getPos() );
}

void AIamCaptureTest::mouseDrag( MouseEvent event )
{
	mMayaCam.mouseDrag( event.getPos(), event.isLeftDown(), event.isMiddleDown(), event.isRightDown() );
}

void AIamCaptureTest::resize()
{
	CameraPersp cam = mMayaCam.getCamera();
	cam.setAspectRatio( getWindowAspectRatio() );
	mMayaCam.setCurrentCam( cam );
}


void AIamCaptureTest::keyDown( KeyEvent event )
{
	switch ( event.getCode() )
	{
		case KeyEvent::KEY_f:
			if ( !isFullScreen() )
			{
				setFullScreen( true );
				if ( mParams.isVisible() )
					showCursor();
				else
					hideCursor();
			}
			else
			{
				setFullScreen( false );
				showCursor();
			}
			break;

		case KeyEvent::KEY_s:
			mParams.show( !mParams.isVisible() );
			if ( isFullScreen() )
			{
				if ( mParams.isVisible() )
					showCursor();
				else
					hideCursor();
			}
			break;

		case KeyEvent::KEY_v:
			 mVerticalSyncEnabled = !mVerticalSyncEnabled;
			 break;

		case KeyEvent::KEY_ESCAPE:
			quit();
			break;

		default:
			break;
	}
}

CINDER_APP_BASIC( AIamCaptureTest, RendererGl )

