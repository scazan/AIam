import re

class BvhWriter:
    def __init__(self, bvh_reader):
        self._bvh_reader = bvh_reader
        self._input_path = bvh_reader.filename
        self._read_header()
        self._read_frame_time()
        self._frames = []

    def _read_header(self):
        self._header = ""
        for line in open(self._input_path):
            line = line.rstrip("\r\n")
            if line == "MOTION":
                return
            self._header += line + "\n"

    def _read_frame_time(self):
        for line in open(self._input_path):
            line = line.rstrip("\r\n")
            m = re.match('^Frame Time:\s+([\d.]+)$', line)
            if m:
                self._frame_time = float(m.group(1))
                return
        raise Exception("failed to get frame time for input file %r" % input_path)

    def add_frame(self, frame):
        self._frames.append(frame)

    def write(self, output_path):
        output = open(output_path, "w")
        print >>output, self._header
        print >>output, "MOTION"
        print >>output, "Frames: %d" % len(self._frames)
        print >>output, "Frame Time: %f" % self._frame_time
        for frame in self._frames:
            self._write_frame(output, frame)

    def _write_frame(self, output, frame):
        for value in frame:
            print >>output, value,
        print >>output

