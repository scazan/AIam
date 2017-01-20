#if (ONI_PLATFORM == ONI_PLATFORM_MACOSX)
#include <GLUT/glut.h>
#else
#include <GL/glut.h>
#endif

class Boids : public ProcessingMethod {
public:
	Boids(int width, int height, int depthThreshold) : ProcessingMethod(width, height, depthThreshold) {
		for(int i=0; i<1; i++) {
			Boid boid;
			boid.x = (float)rand() / RAND_MAX;
			boid.y = (float)rand() / RAND_MAX;
			boids.push_back(boid);
		}
	}

	void processDepthFrame(openni::VideoFrameRef depthFrame) {
	  const openni::DepthPixel* pOniRow;
	  int rowSize = depthFrame.getStrideInBytes() / sizeof(openni::DepthPixel);
	  openni::DepthPixel minDepth = MAX_DEPTH;
	  openni::DepthPixel maxDepth = 0;
	  openni::DepthPixel depth;

    pOniRow = (const openni::DepthPixel*) depthFrame.getData();
	  for (int y = 0; y < height; ++y) {
	    const openni::DepthPixel* pOni = pOniRow;
	    for (int x = 0; x < width; ++x, ++pOni) {
	      if (*pOni != 0) {
	        depth = *pOni;
	        minDepth = MIN(minDepth, depth);
	        maxDepth = MAX(maxDepth, depth);
	      }
	    }
	    pOniRow += rowSize;
	  }

	  float relativeDepth;
	  float x, y;
	  float norm;
		for(vector<Boid>::iterator boid = boids.begin(); boid != boids.end(); boid++) {
		  boid->fx = 0;
		  boid->fy = 0;

      pOniRow = (const openni::DepthPixel*) depthFrame.getData();
	    for (int py = 0; py < height; ++py) {
	      y = (float)py / height;
	      const openni::DepthPixel* pOni = pOniRow;
	      for (int px = 0; px < width; ++px, ++pOni) {
	        x = (float)px / width;
	        if (*pOni != 0) {
	          depth = *pOni;
	          relativeDepth = ((float)depth - minDepth) / (maxDepth - minDepth);
	          if(relativeDepth < 0.0001)
	            relativeDepth = 0.0001;
	          boid->fx += (x - boid->x) / relativeDepth;
            boid->fy += (y - boid->y) / relativeDepth;
	        }
	      }
	      pOniRow += rowSize;
	    }

	    norm = sqrt(boid->fx*boid->fx + boid->fy*boid->fy);
	    if(norm > 0) {
	      boid->x += boid->fx / norm * 0.01;
        boid->y += boid->fy / norm * 0.01;
	    }
		}
	}

	void render() {
		glPointSize(3);
		glColor3f(0,1,0);
		glBegin(GL_POINTS);
		for(vector<Boid>::iterator boid = boids.begin(); boid != boids.end(); boid++) {
			glVertex2f(boid->x, boid->y);
		}
		glEnd();
	}

  void onKey(unsigned char key) {}

private:
  class Boid {
  public:
  	float x, y;
  	float fx, fy;
  };

  vector<Boid> boids;
};
