#ifndef _Topology_hpp_
#define _Topology_hpp_

#include <vector>

class Topology {
public:
  typedef struct {
    unsigned int nodeId;
    double strength; // from 0 to 1 where 1 is nearest neighbour
  } Neighbour;

  void getNeighbours(unsigned int nodeId, std::vector<Neighbour> &);
  void setVicinityFactor(float);
  virtual unsigned int getNumNodes() { return 0; }
  virtual float getDistance(unsigned int sourceNodeId, unsigned int targetNodeId) { return 0.0f; }
  virtual void placeCursorAtNode(unsigned int nodeId) {}
  virtual void moveCursorTowardsNode(unsigned int nodeId, float amount) {}

private:
  float vicinityFactor;
};

#endif
