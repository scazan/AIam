#include "Topology.hpp"

void Topology::setVicinityFactor(float _vicinityFactor) {
  vicinityFactor = _vicinityFactor;
}

void Topology::getNeighbours(unsigned int nodeId, std::vector<Neighbour> &neighbours) {
  neighbours.clear();
  if(vicinityFactor > 0) {
    unsigned int numNodes = getNumNodes();
    float distance;
    Neighbour neighbour;
    for(unsigned int neighbourId = 0; neighbourId < numNodes; neighbourId++) {
      if(neighbourId != nodeId) {
        distance = getDistance(nodeId, neighbourId);
        if(distance < vicinityFactor) {
          neighbour.nodeId = neighbourId;
          neighbour.strength = (float) (vicinityFactor - distance) / vicinityFactor;
          neighbours.push_back(neighbour);
        }
      }
    }
  }
}

