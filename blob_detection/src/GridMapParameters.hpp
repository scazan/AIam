#ifndef GRIDMAPPARAMETERS_HPP
#define GRIDMAPPARAMETERS_HPP

class GridMapParameters {
public:
  GridMapParameters();
  int gridWidth;
  int gridHeight;
  float neighbourhoodParameter;
  float updateParameter;
};

#endif // GRIDMAPPARAMETERS_HPP
