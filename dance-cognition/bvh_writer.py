class BvhWriter:
    def __init__(self, skeleton, frame_time):
        self._root_joint = skeleton.get_root_joint()
        self._frame_time = frame_time
        self._frames = []

    def add_frame(self, frame):
        self._frames.append(frame)

    def write(self, output_path):
        self._output = open(output_path, "w")
        self._write_header()
        self._write("MOTION\n")
        self._write("Frames: %d\n" % len(self._frames))
        self._write("Frame Time: %f\n" % self._frame_time)
        for frame in self._frames:
            self._write_frame(frame)
        self._output.close()

    def _write_header(self):
        self._write("HIERARCHY\n")
        self._indent = 0
        self._write_joint_header(self._root_joint, is_root=True)
        self._write("\n")
    
    def _write_joint_header(self, joint, is_root=False):
        self._write_indent()
        if is_root:
            self._write("ROOT %s" % joint.name)
        else:
            if len(joint.channels) == 0:
                self._write("End Site")
            else:
                self._write("JOINT %s" % joint.name)
        self._write("\n")
        self._write_indent()
        self._write("{\n")
        self._indent += 1

        self._write_indent()
        self._write("OFFSET\t%.4f\t%.4f\t%.4f\n" % (
                joint.translation[0], joint.translation[1], joint.translation[2]))

        if len(joint.channels) > 0:
            self._write_indent()
            self._write("CHANNELS %d %s\n" % (len(joint.channels), " ".join(joint.channels)))

        for child in joint.children:
            self._write_joint_header(child)

        self._indent -= 1
        self._write_indent()
        self._write("}\n")

    def _write_indent(self):
        self._write("\t" * self._indent)

    def _write_frame(self, frame):
        for value in frame:
            self._write("%s " % value)
        self._write("\n")

    def _write(self, string):
        self._output.write(string)
