import subprocess
import tempfile
import random
import time

utterance = "I'm sorry"

def potentially_add_emph(word):
    if random.random() < 0.3:
        return "<EMPH>%s</EMPH>" % word
    else:
        return word

def generate_utterance_as_tempfile():
    words = utterance.split(" ")
    words = [
        potentially_add_emph(word)
        for word in words]
    speed = random.uniform(-50, 50)
    pitch = random.uniform(-50, 50)
    f = tempfile.NamedTemporaryFile(suffix=".sable")
    sable = '''<?xml version="1.0"?>
<!DOCTYPE SABLE PUBLIC "-//SABLE//DTD SABLE speech mark up//EN" 
      "Sable.v0_2.dtd"
[]>
<SABLE>
<SPEAKER NAME="us1_mbrola">

<PITCH BASE="%s%%"><RATE SPEED="%s%%">%s</RATE></PITCH>

</SPEAKER>
</SABLE>
    ''' % (pitch, speed, " ".join(words))
    f.write(sable)
    f.flush()
    # print sable
    return f

def speak_utterance_from_tempfile(f):
    process = subprocess.Popen("festival", shell=True, stdin=subprocess.PIPE)
    process.stdin.write('(tts "%s" \'sable)\n(quit)\n' % f.name)
    process.wait()


while True:
    f = generate_utterance_as_tempfile()
    speak_utterance_from_tempfile(f)
    time.sleep(1)
