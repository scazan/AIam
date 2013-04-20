/*
 Copyright (C) 2013 Gabor Papp

 This program is free software; you can redistribute it and/or modify
 it under the terms of the GNU General Public License as published by
 the Free Software Foundation; either version 3 of the License, or
 (at your option) any later version.

 This program is distributed in the hope that it will be useful,
 but WITHOUT ANY WARRANTY; without even the implied warranty of
 MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
 GNU General Public License for more details.

 You should have received a copy of the GNU General Public License
 along with this program. If not, see <http://www.gnu.org/licenses/>.
*/

#include "boost/date_time.hpp"

#include "cinder/Cinder.h"
#include "cinder/app/AppBasic.h"
#include "cinder/gl/gl.h"
#include "cinder/gl/Texture.h"
#include "cinder/Rect.h"

#include "mndlkit/params/PParams.h"
#include "CiNI.h"
#include "OscClient.h"

using namespace ci;
using namespace ci::app;
using namespace std;

class AIInputApp : public AppBasic
{
	public:
		void prepareSettings( Settings *settings );
		void setup();
		void shutdown();

		void keyDown( KeyEvent event );

		void update();
		void draw();

	private:
		mndl::params::PInterfaceGl mParams;

		float mFps;
		bool mVerticalSyncEnabled;

		void loadOniCB();
		void saveOniCB();
		void openKinectCB();
		std::shared_ptr< std::thread > mThreadRef;
		std::mutex mNIMutex;
		void openKinect( const fs::path &path = fs::path() );
		mndl::ni::OpenNI mNI;
		mndl::ni::UserTracker mNIUserTracker;

		string mNIProgress;

		gl::Texture mDepthTexture;

		enum
		{
			SOURCE_RECORDING = 0,
			SOURCE_KINECT
		};
		int mSource;
		void setupParams();
		bool mMirrored;

		mndl::osc::Client mSender;
};

void AIInputApp::prepareSettings( Settings *settings )
{
	settings->setWindowSize( 800, 600 );
}

void AIInputApp::setup()
{
	mndl::params::PInterfaceGl::load( "params.xml" );
	mParams = mndl::params::PInterfaceGl( "Parameters", Vec2i( 200, 300 ) );
	mParams.addPersistentSizeAndPosition();
	setupParams();

	mSender = mndl::osc::Client( "127.0.0.1", 7891 );
}

void AIInputApp::setupParams()
{
	mndl::params::PInterfaceGl::save();
	mParams.clear();

	mParams.addParam( "Fps", &mFps, "", true );
	mParams.addPersistentParam( "Vertical sync", &mVerticalSyncEnabled, false );
	mParams.addSeparator();

	// FIXME: switching often hangs up, Cinder-NI or OpenNI problem?
	vector< string > enumNames = { "Recording", "Kinect" };
	mParams.addPersistentParam( "Source", enumNames, &mSource, SOURCE_RECORDING );
	mParams.addPersistentParam( "Mirror", &mMirrored, false );

	mNIProgress = "";
	if ( mSource == SOURCE_RECORDING )
		mParams.addButton( "Load video", std::bind( &AIInputApp::loadOniCB, this ) );
	else
		mParams.addButton( "Save video", std::bind( &AIInputApp::saveOniCB, this ) );
	mParams.addParam( "Progress", &mNIProgress, "", true );

}

void AIInputApp::update()
{
	mFps = getAverageFps();

	if ( mVerticalSyncEnabled != gl::isVerticalSyncEnabled() )
		gl::enableVerticalSync( mVerticalSyncEnabled );

	static int lastSource = -1;
	if ( mSource != lastSource )
	{
		setupParams();
		if ( mSource == SOURCE_KINECT )
			openKinectCB();

		lastSource = mSource;
	}

	{
		std::lock_guard< std::mutex > lock( mNIMutex );

		if ( mNI )
		{
			if ( mNI.checkNewDepthFrame() )
				mDepthTexture = mNI.getDepthImage();

			if ( mMirrored != mNI.isMirrored() )
				mNI.setMirrored( mMirrored );
		}
	}
}

void AIInputApp::draw()
{
	gl::clear();
	gl::setViewport( getWindowBounds() );
	gl::setMatricesWindow( getWindowSize() );

	gl::color( Color::white() );
	if ( mDepthTexture )
		gl::draw( mDepthTexture, getWindowBounds() );

	{
		std::lock_guard< std::mutex > lock( mNIMutex );
		if ( mNI )
		{
			RectMapping mapping( Rectf( 0, 0, 640, 480), getWindowBounds() );

			gl::color( Color( 1, 0, 0 ) );
			vector< unsigned > users = mNIUserTracker.getUsers();
			if ( !users.empty() )
			{
				unsigned id = users[ 0 ];

				float torsoConf;
				Vec2f torso2d = mNIUserTracker.getJoint2d( id, XN_SKEL_TORSO, &torsoConf );
				gl::drawSolidCircle( mapping.map( torso2d ), 3 );

				Vec3f torso3d = mNIUserTracker.getJoint3d( id, XN_SKEL_TORSO, &torsoConf );
				if ( torsoConf > .9f )
				{
					mndl::osc::Message msg( "/joint/torso" );
					msg.addArg( torso3d.x );
					msg.addArg( torso3d.y );
					msg.addArg( torso3d.z );
					mSender.send( msg );
				}
			}
		}
	}

	mParams.draw();
}

void AIInputApp::loadOniCB()
{
	ci::fs::path appPath( ci::app::getAppPath() );
#ifdef CINDER_MAC
	appPath = appPath.parent_path();
#endif
	vector< string > extensions;
	extensions.push_back( "oni" );
	ci::fs::path oniPath = ci::app::getOpenFilePath( appPath, extensions );

	if ( !oniPath.empty() )
	{
		if ( mThreadRef )
			mThreadRef->join();
		mNIUserTracker.reset();
		mNI.reset();
		mNIProgress = "Loading";
		mThreadRef = shared_ptr< thread >( new thread( bind( &AIInputApp::openKinect, this, oniPath ) ) );
	}
}

void AIInputApp::saveOniCB()
{
	if ( !mNI )
		return;

	if ( mNI.isRecording() )
	{
		mParams.setOptions( "Save video", "label=`Save video`" );
		mNI.stopRecording();
	}
	else
	{
		mParams.setOptions( "Save video", "label=`Finish saving`" );

		ci::fs::path appPath = ci::app::getAppPath();
#ifdef CINDER_MAC
		appPath = appPath.parent_path();
#endif
		boost::posix_time::ptime now = boost::posix_time::second_clock::local_time();
		string timestamp = boost::posix_time::to_iso_string( now );

		mNI.startRecording( appPath / ci::fs::path( "capture-" + timestamp + ".oni" ) );
	}
}

void AIInputApp::openKinectCB()
{
	if ( mThreadRef )
		mThreadRef->join();
	mNIUserTracker.reset();
	mNI.reset();
	mNIProgress = "Connecting";
	mThreadRef = shared_ptr< thread >( new thread( bind( &AIInputApp::openKinect, this, fs::path() ) ) );
}

void AIInputApp::openKinect( const fs::path &path )
{
	if ( mNI )
		mNI.stop();

    try
    {
		mndl::ni::OpenNI kinect;
		mndl::ni::OpenNI::Options options;
		options.enableDepth( true ).enableUserTracker( true ).enableImage( false ).enableIR( false );


		if ( path.empty() )
			kinect = mndl::ni::OpenNI( mndl::ni::OpenNI::Device(), options );
		else
			kinect = mndl::ni::OpenNI( path );
        {
            std::lock_guard< std::mutex > lock( mNIMutex );
            mNI = kinect;
        }
    }
    catch ( const mndl::ni::OpenNIExc &exc )
    {
		if ( path.empty() )
			mNIProgress = "No device detected";
		else
			mNIProgress = "Could not load recording";
        return;
    }

	if ( path.empty() )
		mNIProgress = "Connected";
	else
		mNIProgress = "Recording loaded";
    {
        std::lock_guard< std::mutex > lock( mNIMutex );
        mNI.start();
        mNIUserTracker = mNI.getUserTracker();
        //mNIUserTracker.addListener( this );
    }
}

void AIInputApp::keyDown( KeyEvent event )
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
			mndl::params::PInterfaceGl::showAllParams( !mParams.isVisible() );
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

void AIInputApp::shutdown()
{
	mndl::params::PInterfaceGl::save();
	if ( mThreadRef )
		mThreadRef->join();
}

CINDER_APP_BASIC( AIInputApp, RendererGl )

