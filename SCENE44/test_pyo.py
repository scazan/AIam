from audio import *
import time

s = create_audio_server().boot()
# s.amp = 0.1
sine1 = Sine(freq=[440,440]).range(.5,.9).out()
# sine2 = Sine(freq=[660,660]).out()

# def process():
#     s.amp *= 0.9

# pat = Pattern(time=0.01, function=process).play()

# noise = PinkNoise([10,10]).out()

#s.gui(locals())

s.start()

while True:
    time.sleep(1)
