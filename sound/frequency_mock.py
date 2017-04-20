import sys, os
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__))+"/../SCENE44")
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__))+"/../dance-cognition")

from audio import *
import window
import argparse
from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import *

s = create_audio_server().boot()
s.amp = 0.1
sine_left = Sine()
sine_right = Sine()
left = sine_left.out()
right = sine_right.out(1)

min_freq = 0
max_freq = 2500

def update_sound(control_value):
        freq = min_freq + (max_freq - min_freq) * control_value**5
        sine_left.setFreq(freq)
        sine_right.setFreq(freq)

update_sound(0)

class SoundWindow(window.Window):
	def InitGL(self):
		window.Window.InitGL(self)
		glutMotionFunc(self._mouse_moved)
		glClearColor(0,0,0,0)

	def _mouse_moved(self, x, y):
		control_value = float(y) / self.window_height
		update_sound(control_value)

	def render(self):
		pass

parser = argparse.ArgumentParser()
window.Window.add_parser_arguments(parser)
args = parser.parse_args()

s.start()
window.run(SoundWindow, args)
