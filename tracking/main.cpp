#include "Tracker.hpp"

int main(int argc, char **argv) {
  Tracker tracker;
  openni::Status status = tracker.init();
  if (status != openni::STATUS_OK)
    return 1;
  tracker.mainLoop();
}
