#include "GridMap.hpp"
#include "RectGridTopology.hpp"

using namespace std;

GridMap::GridMap(int _inputSize, const GridMapParameters &_gridMapParameters) {
  inputSize = _inputSize;
  topology = new RectGridTopology(_gridMapParameters.gridWidth,
				  _gridMapParameters.gridHeight);
  gridMapParameters = _gridMapParameters;
  createSom();
  createSomInput();
  createSomOutput();
}

void GridMap::setRandomModelValues() {
  som->setRandomModelValues();
}

void GridMap::createSom() {
  som = new SOM(inputSize, topology);
}

void GridMap::createSomInput() {
  for(int i = 0; i < inputSize; i++)
    somInput.push_back(0);
}

void GridMap::createSomOutput() {
  for(unsigned int i = 0; i < topology->getNumNodes(); i++)
    somOutput.push_back(0);
}

const float* GridMap::getModel(unsigned int x, unsigned int y) const {
  unsigned int nodeId = ((RectGridTopology*) topology)->gridCoordinatesToId(x, y);
  return som->getModel(nodeId);
}
