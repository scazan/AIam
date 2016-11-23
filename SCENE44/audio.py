from pyo import *
import pyaudio

def create_audio_server(device_name='default'):
    device_index = _get_device_index(device_name)
    server = Server()
    server.setInOutDevice(device_index)
    return server

def _get_device_index(device_name):
    p = pyaudio.PyAudio()
    for i in range(p.get_device_count()):
        device_info = p.get_device_info_by_index(i)
        if device_info['name'] == device_name:
            return i
    raise Exception("failed to find audio device with name '%s'" % device_name)

