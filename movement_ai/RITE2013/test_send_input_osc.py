from osc_sender import OscSender

osc_sender = OscSender(50001)
osc_sender.send("/input_position", 0.3, 0.6, -0.5)
