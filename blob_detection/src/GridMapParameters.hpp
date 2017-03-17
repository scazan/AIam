#ifndef GRIDMAPPARAMETERS_HPP
#define GRIDMAPPARAMETERS_HPP

class GridMapParameters {
public:
  GridMapParameters();
  int gridWidth;
  int gridHeight;
  float neighbourhoodParameter;
  float learningParameter;
};

#endif // GRIDMAPPARAMETERS_HPP
