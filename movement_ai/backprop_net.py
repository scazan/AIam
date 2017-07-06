from pybrain.tools.shortcuts import buildNetwork
from pybrain.supervised.trainers import BackpropTrainer
from pybrain.datasets import SupervisedDataSet

class BackpropNet:
    def __init__(self, input_size, hidden_layer_size, output_size):
        self._input_size = input_size
        self._output_size = output_size
        self._net = buildNetwork(input_size, hidden_layer_size, output_size)
        self._trainer = BackpropTrainer(self._net, learningrate=0.001)

    def process(self, inp):
        return self._net.activate(inp)

    def train(self, inp, output):
        dataset = SupervisedDataSet(self._input_size, self._output_size)
        dataset.addSample(inp, output)
        self._trainer.trainOnDataset(dataset)
