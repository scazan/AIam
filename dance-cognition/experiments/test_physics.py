import unittest
from physics import FrictionConstrainer
from numpy import array

class MockBalanceDetector:
    def __init__(self):
        self.supporting_index = 0

    def identify_supporting_vertex(self, vertices):
        return self.supporting_index

class FrictionConstrainerTest(unittest.TestCase):
    def test_dont_constrain_first_frame(self):
        self.when_input_frames([
            [" Q    ",
             " o    ",
             "      "],
            ])
        self.expect_output_frames([
            [" Q    ",
             " o    ",
             "      "],
            ])

    def test_constrain_second_frame(self):
        self.when_input_frames([
            [" Q    ",
             " o    ",
             "      "],

            ["      ",
             "  Q   ",
             "  o   "],
            ])
        self.expect_output_frames([
            [" Q    ",
             " o    ",
             "      "],

            [" Q    ",
             " o    ",
             "      "],
            ])

    def test_constrain_third_frame(self):
        self.when_input_frames([
            [" Q    ",
             " o    ",
             "      "],

            ["      ",
             "  Q   ",
             "  o   "],

            ["      ",
             "   Q  ",
             "   o  "],
            ])
        self.expect_output_frames([
            [" Q    ",
             " o    ",
             "      "],

            [" Q    ",
             " o    ",
             "      "],

            [" Q    ",
             " o    ",
             "      "],
            ])

    def test_move_unsupported_vertex(self):
        self.when_input_frames([
            [" Q    ",
             " o    ",
             "      "],

            ["      ",
             "  Q   ",
             "   o  "],
            ])
        self.expect_output_frames([
            [" Q    ",
             " o    ",
             "      "],

            [" Q    ",
             "  o   ",
             "      "],
            ])

    def test_switch_balance(self):
        self.when_input_frames([
            [" Q    ",
             " o    ",
             "      "],

            ["      ",
             "  Q   ",
             "   o  "],

            ["      ",
             "  q   ",
             "    O "],

            ["      ",
             "   q  ",
             "    O "],
            ])
        self.expect_output_frames([
            [" Q    ",
             " o    ",
             "      "],

            [" Q    ",
             "  o   ",
             "      "],

            [" q    ",
             "   O  ",
             "      "],

            ["  q   ",
             "   O  ",
             "      "],
            ])

    def when_input_frames(self, frames):
        self.balance_detector = MockBalanceDetector()
        self.constrainer = FrictionConstrainer(self.balance_detector)
        self.input_frames = frames

    def expect_output_frames(self, expected_output_frames):
        for frame_index in range(len(expected_output_frames)):
            input_frame = self.input_frames[frame_index]
            expected_output_frame = expected_output_frames[frame_index]
            input_vertices = self.frame_to_vertices(input_frame)
            self.balance_detector.supporting_index = self.frame_to_supporting_index(input_frame)
            output_vertices = self.constrainer.constrain(input_vertices)
            output_frame = self.vertices_to_frame(output_vertices,
                                                  self.balance_detector.supporting_index)
            if output_frame != expected_output_frame:
                raise AssertionError("in frame %s, expected %s but got %s" % (
                        frame_index,
                        self.str_frame(expected_output_frame),
                        self.str_frame(output_frame)))

    def frame_to_vertices(self, frame):
        return [self.find_vertex_in_frame(frame, ["o","O"]),
                self.find_vertex_in_frame(frame, ["q","Q"])]

    def find_vertex_in_frame(self, frame, symbols):
        y = 0
        for row in frame:
            x = 0
            for symbol in row:
                if symbol in symbols:
                    return array([x, y])
                x += 1
            y += 1
        raise Exception("find_vertex_in_frame(%s, %s) failed" % (frame, symbols))

    def frame_to_supporting_index(self, frame):
        y = 0
        for row in frame:
            x = 0
            for symbol in row:
                if symbol == "O":
                    return 0
                elif symbol == "Q":
                    return 1
                x += 1
            y += 1
        raise Exception("frame_to_supporting_index(%s) failed" % frame)

    def vertices_to_frame(self, vertices, supporting_index):
        frame = [
            "      ",
            "      ",
            "      "]
        frame = self.add_symbol_to_frame(frame, vertices, supporting_index, 0, "o", "O")
        frame = self.add_symbol_to_frame(frame, vertices, supporting_index, 1, "q", "Q")
        return frame

    def add_symbol_to_frame(self, frame, vertices, supporting_index, vertex_index,
                            normal_symbol, supporting_symbol):
        x, y = vertices[vertex_index]
        if 0 <= x < 6 and 0 <= y < 3:
            if supporting_index == vertex_index:
                symbol = supporting_symbol
            else:
                symbol = normal_symbol
            frame[y] = frame[y][0:x] + symbol + frame[y][x+1:6]
        return frame

    def str_frame(self, frame):
        return "\n%s\n" % ("\n".join(["'%s'" % row for row in frame]))
