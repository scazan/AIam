import cPickle

def save(data, filename):
    print "saving %s..." % filename
    f = open(filename, "w")
    cPickle.dump(data, f)
    f.close()
    print "ok"

def load(filename):
    print "loading %s..." % filename
    f = open(filename)
    data = cPickle.load(f)
    f.close()
    print "ok"
    return data
