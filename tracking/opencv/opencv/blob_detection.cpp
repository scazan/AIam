#include <opencv2/core/core.hpp>
#include <opencv2/highgui/highgui.hpp>
#include <opencv2/features2d/features2d.hpp>

using namespace cv;

int main(int argc, char **argv) {
  // Read image
  Mat im = imread( "frame.png" );
 
  SimpleBlobDetector::Params params;
  params.filterByColor = false;
  params.filterByArea = true;
  params.minArea = 65*65;
  params.maxArea = 180*180;
  params.filterByCircularity = false;
  params.filterByInertia = false;
  params.filterByConvexity = false;

  SimpleBlobDetector detector(params);
 
  // Detect blobs.
  std::vector<KeyPoint> keypoints;
  detector.detect( im, keypoints);
 
  // Draw detected blobs as red circles.
  // DrawMatchesFlags::DRAW_RICH_KEYPOINTS flag ensures the size of the circle corresponds to the size of blob
  Mat im_with_keypoints;
  drawKeypoints( im, keypoints, im_with_keypoints, Scalar(0,0,255), DrawMatchesFlags::DRAW_RICH_KEYPOINTS );
 
  // Show blobs
  imshow("keypoints", im_with_keypoints );
  waitKey(0);
}
