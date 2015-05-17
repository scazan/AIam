import cPickle

def save_model(model, filename):
    print "saving model %s..." % filename
    f = open(filename, "w")
    cPickle.dump(model, f)
    f.close()
    print "ok"

def load_model(filename):
    print "loading model %s..." % filename
    f = open(filename)
    model = cPickle.load(f)
    f.close()
    print "ok"
    return model

def save_training_data(training_data, filename):
    print "saving training data %s..." % filename
    f = open(filename, "w")
    cPickle.dump(training_data, f)
    f.close()
    print "ok"

def load_training_data(filename):
    print "loading training data %s..." % filename
    f = open(filename)
    training_data = cPickle.load(f)
    f.close()
    print "ok"
    return training_data
