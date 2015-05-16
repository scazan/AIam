#ifndef _TRACKER_HPP_
#define _TRACKER_HPP_

#include "NiTE.h"

#define MAX_USERS 10

class Tracker {
public:
  Tracker();
  virtual ~Tracker();

  virtual openni::Status init();
  virtual openni::Status mainLoop();

private:
  class User {
  public:
    User();
    void updateState(const nite::UserData& user, uint64_t ts);

  private:
    void debug(const char *message, uint64_t ts);
    nite::UserId id;
    bool visible;
    nite::SkeletonState skeletonState;
  };

  void processFrame();

  openni::Device device;
  nite::UserTracker* userTracker;
  User users[MAX_USERS];
};


#endif // _TRACKER_HPP_
