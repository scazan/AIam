#ifndef GRIDMAP_HPP
#define GRIDMAP_HPP

#include "GridMapParameters.hpp"
#include "SOM.hpp"

class GridMap {
public:
  GridMap(int inputSize, const GridMapParameters &);
  void setRandomModelValues();
  const float* getModel(unsigned int x, unsigned int y) const;

protected:
  GridMapParameters gridMapParameters;
  void createSom();
  void createSomInput();
  void createSomOutput();

  int inputSize;
  SOM *som;
  Topology *topology;
  SOM::Sample somInput;
  SOM::Output somOutput;
};

#endif // GRIDMAP_HPP
