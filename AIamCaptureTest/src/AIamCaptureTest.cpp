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
#include "cinder/gl/DisplayList.h"
#include "cinder/Camera.h"
#include "cinder/MayaCamUI.h"
#include "cinder/TriMesh.h"

#include "mndlkit/params/PParams.h"

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

		void shutdown();
		void keyDown( KeyEvent event );
		void mouseDown( MouseEvent event );
		void mouseDrag( MouseEvent event );
		void resize();

		void update();
		void draw();

	private:
		mndl::params::PInterfaceGl mParams;

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

		static const int PLANE_SIZE = 1024;
		TriMesh createSquare( const Vec2i &resolution );
		TriMesh mTriMeshPlane;
		void createGrid();
		gl::DisplayList mGrid;

		bool mDrawAxes;
		bool mDrawPlane;
		bool mDrawGrid;
		int mGridSize;
};

void AIamCaptureTest::prepareSettings( Settings *settings )
{
	settings->setWindowSize( 800, 600 );
}

void AIamCaptureTest::setup()
{
	mndl::params::PInterfaceGl::load( "params.xml" );
	mParams = mndl::params::PInterfaceGl( "Parameters", Vec2i( 200, 300 ) );
	mParams.addPersistentSizeAndPosition();
	mParams.addParam( "Fps", &mFps, "", true );
	mParams.addParam( "Vertical sync", &mVerticalSyncEnabled );
	mParams.addSeparator();

	CameraPersp cam;
	cam.setPerspective( 60, getWindowAspectRatio(), 0.1f, 10000.0f );
	cam.setEyePoint( Vec3f( 0, 30, 260 ) );
	cam.setCenterOfInterestPoint( Vec3f( 0, 70, 0 ) );
	mMayaCam.setCurrentCam( cam );

	mParams.addPersistentParam( "Draw axes", &mDrawAxes, true );
	mParams.addPersistentParam( "Draw plane", &mDrawPlane, true );
	mParams.addPersistentParam( "Draw grid", &mDrawGrid, true );
	mParams.addPersistentParam( "Grid size", &mGridSize, 50, "min=1 max=512" );
	mParams.addSeparator();

	mTriMeshPlane = createSquare( Vec2i( 64, 64 ) );

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

	static int lastGridSize = -1;
	if ( lastGridSize != mGridSize )
	{
		createGrid();
		lastGridSize = mGridSize;
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

		if ( mDrawAxes )
			gl::drawCoordinateFrame( 10.f, 2.f, 0.5f );

		glPolygonOffset( 1.0f, 1.0f );
		gl::enable( GL_POLYGON_OFFSET_FILL );
		if ( mMotions[ mMotionIndex ] )
		{
			mMotions[ mMotionIndex ]->draw();
		}

		if ( mDrawPlane )
		{
			gl::pushModelView();
			gl::color( Color::gray( .8f ) );
			gl::scale( Vec3f( PLANE_SIZE, 1.f, PLANE_SIZE ) );
			gl::draw( mTriMeshPlane );
			gl::popModelView();
		}
		gl::disable( GL_POLYGON_OFFSET_FILL );

		if ( mDrawGrid && mGrid )
		{
			gl::pushModelView();
			gl::color( Color::black() );
			mGrid.draw();
			gl::popModelView();
		}
	}

	mndl::params::PInterfaceGl::draw();
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

// based on Cinder-MeshHelper by Ban the Rewind
// https://github.com/BanTheRewind/Cinder-MeshHelper/
TriMesh AIamCaptureTest::createSquare( const Vec2i &resolution )
{
	vector< uint32_t > indices;
	vector< Vec3f > normals;
	vector< Vec3f > positions;
	vector< Vec2f > texCoords;

	Vec3f norm0( 0.0f, 1.0f, 0.0f );

	Vec2f scale( 1.0f / math< float >::max( (float)resolution.x, 1.0f ),
				 1.0f / math<float>::max( (float)resolution.y, 1.0f ) );
	uint32_t index = 0;
	for ( int32_t y = 0; y < resolution.y; ++y )
	{
		for ( int32_t x = 0; x < resolution.x; ++x, ++index )
		{
			float x1 = (float)x * scale.x;
			float y1 = (float)y * scale.y;
			float x2 = (float)( x + 1 ) * scale.x;
			float y2 = (float)( y + 1 ) * scale.y;

			Vec3f pos0( x1 - 0.5f, 0.0f, y1 - 0.5f );
			Vec3f pos1( x2 - 0.5f, 0.0f, y1 - 0.5f );
			Vec3f pos2( x1 - 0.5f, 0.0f, y2 - 0.5f );
			Vec3f pos3( x2 - 0.5f, 0.0f, y2 - 0.5f );

			Vec2f texCoord0( x1, y1 );
			Vec2f texCoord1( x2, y1 );
			Vec2f texCoord2( x1, y2 );
			Vec2f texCoord3( x2, y2 );

			positions.push_back( pos2 );
			positions.push_back( pos1 );
			positions.push_back( pos0 );
			positions.push_back( pos1 );
			positions.push_back( pos2 );
			positions.push_back( pos3 );

			texCoords.push_back( texCoord2 );
			texCoords.push_back( texCoord1 );
			texCoords.push_back( texCoord0 );
			texCoords.push_back( texCoord1 );
			texCoords.push_back( texCoord2 );
			texCoords.push_back( texCoord3 );

			for ( uint32_t i = 0; i < 6; ++i )
			{
				indices.push_back( index * 6 + i );
				normals.push_back( norm0 );
			}
		}
	}

	TriMesh mesh;

	mesh.appendIndices( &indices[ 0 ], indices.size() );
	for ( auto normal: normals )
	{
		mesh.appendNormal( normal );
	}

	mesh.appendVertices( &positions[ 0 ], positions.size() );

	for ( auto texCoord: texCoords )
	{
		mesh.appendTexCoord( texCoord );
	}

	return mesh;
}

void AIamCaptureTest::createGrid()
{
	mGrid = gl::DisplayList( GL_COMPILE );
	mGrid.newList();
	gl::color( Color::black() );
	int n = PLANE_SIZE / mGridSize;
	Vec3f step( mGridSize, 0, 0 );
	Vec3f p( 0, 0, -PLANE_SIZE * .5f );
	p -= step * n / 2;
	for ( int i = 0; i < n; i++ )
	{
		gl::drawLine( p, p + Vec3f( 0, 0, PLANE_SIZE ) );
		p += step;
	}
	step = Vec3f( 0, 0, mGridSize );
	p = Vec3f( -PLANE_SIZE * .5f, 0, 0 );
	p -= step * n / 2;
	for ( int i = 0; i < n; i++ )
	{
		gl::drawLine( p, p + Vec3f( PLANE_SIZE, 0, 0 ) );
		p += step;
	}
	mGrid.endList();
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

void AIamCaptureTest::shutdown()
{
	mndl::params::PInterfaceGl::save();
}

CINDER_APP_BASIC( AIamCaptureTest, RendererGl )

