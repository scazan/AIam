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
