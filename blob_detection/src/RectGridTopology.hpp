#ifndef _RectGridTopology_hpp_
#define _RectGridTopology_hpp_

#include "Topology.hpp"

class RectGridTopology : public Topology {
public:
  typedef struct {
    unsigned int x;
    unsigned int y;
  } Node;

  RectGridTopology(unsigned int gridWidth, unsigned int gridHeight);
  unsigned int getNumNodes();
  float getDistance(unsigned int sourceNodeId, unsigned int targetNodeId);
  unsigned int getGridWidth() { return gridWidth; }
  unsigned int getGridHeight() { return gridHeight; }
  Node getNode(unsigned int nodeId);
  void placeCursorAtNode(unsigned int nodeId);
  void moveCursorTowardsNode(unsigned int nodeId, float amount);
  unsigned int gridCoordinatesToId(unsigned int x, unsigned int y);
  void idToGridCoordinates(unsigned int id, unsigned int &x, unsigned int &y);
  void getCursorPosition(float &x, float &y);

private:
  unsigned int gridWidth;
  unsigned int gridHeight;
  unsigned int numNodes;
  unsigned int maxDistance;
  float cursorX, cursorY;
};

#endif
