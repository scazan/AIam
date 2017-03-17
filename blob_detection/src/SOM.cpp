#include "SOM.hpp"
#include "Random.hpp"
#include <math.h>
#include <cassert>

using namespace std;

SOM::SOM(uint _inputSize, Topology *_topology) {
  assert(_inputSize != 0);
  inputSize = _inputSize;
  topology = _topology;
  numModels = topology->getNumNodes();
  setLearningParameter(0.5);
  outputMin = 0;
  outputMax = 0;
  maxDistance = ::sqrt((float)inputSize); // sqrt(1� + 1� ... inputSize times)
  createModels();
}

SOM::~SOM() {
  deleteModels();
}

Topology *SOM::getTopology() const {
  return topology;
}

void SOM::createModels() {
  for(uint id = 0; id < numModels; id++)
    models.push_back(new Model(this, id));
}

void SOM::deleteModels() {
  for(vector<Model*>::iterator i = models.begin(); i != models.end(); ++i)
    delete *i;
}

SOM::Sample SOM::createSample(const float *values) const {
  Sample sample(inputSize);
  const float *valuePtr = values;
  Sample::iterator samplePtr = sample.begin();
  for(uint k = 0; k < inputSize; k++)
    *samplePtr++ = *valuePtr++;
  return sample;
}

void SOM::setNeighbourhoodParameter(float _neighbourhoodParameter) {
  neighbourhoodParameter = _neighbourhoodParameter;
  topology->setVicinityFactor(neighbourhoodParameter);
}

void SOM::setLearningParameter(float x) {
  learningParameter = x;
}

const float* SOM::getModel(uint id) const {
  return models[id]->getValues();
}

SOM::uint SOM::getWinner(const Sample &input) const {
  float diff;
  float closest = 0;
  uint winner = 0;
  uint modelIndex = 0;
  Model *model;
  for(vector<Model*>::const_iterator i = models.begin(); i != models.end(); ++i) {
    model = *i;
    diff = model->getDistance(input);
    if(i == models.begin() || diff < closest) {
      closest = diff;
      winner = modelIndex;
    }
    modelIndex++;
  }
  return winner;
}

SOM::uint SOM::getLastWinner() const {
  return lastWinnerId;
}

void SOM::train(const Sample &input) {
  lastWinnerId = getWinnerAndStoreOutput(input, lastOutput);
  Model *winnerModel = models[lastWinnerId];
  winnerModel->updateToInput(input);
}

SOM::uint SOM::getWinnerAndStoreOutput(const Sample &input, Output &output) {
  uint winnerId = 0;
  float distance, localDistanceMin = 0, localDistanceMax = 0;
  float modelOutput, localOutputMin = 0, localOutputMax = 0;
  Model *model;

  output.clear();
  uint modelId = 0;
  for(vector<Model*>::iterator i = models.begin(); i != models.end(); ++i) {
    model = *i;
    distance = model->getDistance(input);
    modelOutput = (float) (::sqrt(distance) / maxDistance);
    if(i == models.begin()) {
      localDistanceMin = localDistanceMax = distance;
      winnerId = modelId;
      localOutputMin = localOutputMax = modelOutput;
    }
    else if(distance < localDistanceMin) {
      localDistanceMin = distance;
      winnerId = modelId;
      localOutputMin = modelOutput;
    }
    else if(distance > localDistanceMax) {
      localDistanceMax = distance;
      localOutputMax = modelOutput;
    }
    output.push_back(modelOutput);
    modelId++;
  }

  outputMin = localOutputMin;
  outputMax = localOutputMax;
  return winnerId;
}

void SOM::getOutput(const Sample &input, Output &output) const {
  ((SOM *)this)->getWinnerAndStoreOutput(input, output);
}

void SOM::getLastOutput(Output &output) const {
  output = lastOutput;
}

float SOM::getOutputMin() const {
  return outputMin;
}

float SOM::getOutputMax() const {
  return outputMax;
}

void SOM::setModel(uint modelIndex, const Sample &sample) {
  models[modelIndex]->set(sample);
}

void SOM::setAllModels(const Sample &sample) {
  Model *model;
  for(vector<Model*>::iterator i = models.begin(); i != models.end(); ++i) {
    model = *i;
    model->set(sample);
  }
}

void SOM::setRandomModelValues(float min, float max) {
  Model *model;
  for(vector<Model*>::iterator i = models.begin(); i != models.end(); ++i) {
    model = *i;
    model->setRandomValues(min, max);
  }
}

void SOM::updateNeighbourLists() {
  for(vector<Model*>::iterator i = models.begin(); i != models.end(); ++i)
    (*i)->updateNeighbourList();
}

SOM::ActivationPattern *SOM::createActivationPattern() const {
  vector<float> *pattern = new vector<float>();
  for(unsigned int i = 0; i < numModels; i++)
    pattern->push_back(0);
  return pattern;
}

void SOM::getActivationPattern(ActivationPattern *activationPattern) const {
  float range = outputMax - outputMin;
  if(range > 0) {
    ActivationPattern::iterator activationPatternNode = activationPattern->begin();
    for(Output::const_iterator lastOutputNode = lastOutput.begin();
	lastOutputNode != lastOutput.end(); lastOutputNode++) {
      *activationPatternNode = 1.0f - (*lastOutputNode - outputMin) / range;
      activationPatternNode++;
    }
  }
  else {
    fill(activationPattern->begin(), activationPattern->end(), 0);
  }
}

void SOM::addNoiseToModels(float amount) {
  for(vector<Model*>::iterator i = models.begin(); i != models.end(); ++i)
    (*i)->addNoise(amount);
}

void SOM::writeModelData(ostream &f) const {
  f << inputSize << endl;
  for(vector<Model*>::const_iterator i = models.begin(); i != models.end(); ++i)
    (*i)->writeData(f);
}


SOM::Model::Model(const SOM *_parent, uint _id) {
  id = _id;
  parent = _parent;
  inputSize = parent->inputSize;
  values = new float [inputSize];
  neighbourhoodParameter = 0;
}

SOM::Model::~Model() {
  delete [] values;
}

void SOM::Model::updateToInput(const SOM::Sample &input) {
  float learningParameter = parent->learningParameter;
  moveTowards(input, learningParameter);

  updateNeighbourList();
  for(std::vector<Neighbour>::iterator i = neighbours.begin(); i != neighbours.end(); i++)
    i->model->moveTowards(input, learningParameter * i->strength);
}

void SOM::Model::moveTowards(const std::vector<float > &sample, float amount) {
  float *valuePtr = values;
  Sample::const_iterator samplePtr = sample.begin();
  for(uint k = 0; k < inputSize; k++) {
    *valuePtr += amount * (*samplePtr - *valuePtr);
    valuePtr++;
    samplePtr++;
  }
}

float SOM::Model::getDistance(const Sample &input) {
  float *valuePtr = values;
  Sample::const_iterator samplePtr = input.begin();
  float d;
  float distance = 0;
  for(uint k = 0; k < inputSize; k++) {
    d = *valuePtr++ - *samplePtr++;
    distance += d * d;
  }
  return distance;
}

void SOM::Model::set(const Sample &sample) {
  float *valuePtr = values;
  Sample::const_iterator samplePtr = sample.begin();
  for(uint k = 0; k < inputSize; k++)
    *valuePtr++ = *samplePtr++;
}

void SOM::Model::setRandomValues(float min, float max) {
  float *valuePtr = values;
  for(uint k = 0; k < inputSize; k++)
    *valuePtr++ = randomInRange(min, max);
}

void SOM::Model::updateNeighbourList() {
  if(neighbourhoodParameter != parent->neighbourhoodParameter) {
    std::vector<Topology::Neighbour> topologyNeighbours;
    parent->topology->getNeighbours(id, topologyNeighbours);
    neighbours.clear();
    Neighbour neighbour;
    for(std::vector<Topology::Neighbour>::iterator i = topologyNeighbours.begin(); i != topologyNeighbours.end(); i++) {
      neighbour.model = parent->models[i->nodeId];
      neighbour.strength = i->strength;
      neighbours.push_back(neighbour);
    }
    neighbourhoodParameter = parent->neighbourhoodParameter;
  }
}

void SOM::Model::addNoise(float amount) {
  float *valuePtr = values;
  for(uint k = 0; k < inputSize; k++) {
    *valuePtr += randomInRange(-amount, amount);
    if(*valuePtr < 0)
      *valuePtr = 0;
    else if(*valuePtr > 1)
      *valuePtr = 1;
    valuePtr++;
  }
}

void SOM::Model::writeData(ostream &f) const {
  float *valuePtr = values;
  for(uint k = 0; k < inputSize; k++)
    f << *valuePtr++ << endl;
}
