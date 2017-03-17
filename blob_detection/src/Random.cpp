#include "Random.hpp"
#include <stdlib.h>

float randomInRange(float min, float max) {
  return min + (max - min) * (float) rand() / RAND_MAX;
}
