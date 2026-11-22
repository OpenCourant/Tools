"""End-to-end regression tests for inp2rad element conversion.

Run from the inp2rad directory with:

    python3 -m unittest discover -s tests -v
"""

import contextlib
import importlib.util
import io
import os
import pathlib
import subprocess
import tempfile
import unittest
from unittest import mock

MODULE = pathlib.Path(__file__).resolve().parents[1] / "inp2rad" / "inp2rad.py"
spec = importlib.util.spec_from_file_location("inp2rad", MODULE)
inp2rad = importlib.util.module_from_spec(spec)
spec.loader.exec_module(inp2rad)
inp2rad.or_gui = False
inp2rad.run_timer = False


def coordinates(element_type, count, dim=3):
    """Return non-degenerate node coordinates for an element family."""
    family = inp2rad.canonical_element_type(element_type)
    if dim == 2:
        if element_type.upper() in inp2rad.TWO_D_TRIANGLES or count <= 3:
            base = [(0, 0), (1, 0), (0, 1)]
        else:
            base = [(0, 0), (1, 0), (1, 1), (0, 1)]
        edges = [(base[i], base[(i + 1) % len(base)])
                 for i in range(len(base))]
        edge = 0
        while len(base) < count:
            a, b = edges[edge % len(edges)]
            base.append(((a[0] + b[0]) / 2.0, (a[1] + b[1]) / 2.0))
            edge += 1
        return base[:count]
    elif family in ("B31", "B32"):
        base = [(0, 0, 0), (1, 0, 0), (0.5, 0, 0)]
    elif family in ("S3", "TRIA"):
        base = [(0, 0, 0), (1, 0, 0), (0, 1, 0)]
    elif family in ("S4", "S6", "S8", "QUAD"):
        base = [(0, 0, 0), (1, 0, 0), (1, 1, 0), (0, 1, 0),
                (0.5, 0, 0), (1, 0.5, 0), (0.5, 1, 0), (0, 0.5, 0)]
    elif family == "C3D4":
        base = [(0, 0, 0), (1, 0, 0), (0, 1, 0), (0, 0, 1)]
    elif family == "C3D10":
        base = [(0, 0, 0), (1, 0, 0), (0, 1, 0), (0, 0, 1),
                (0.5, 0, 0), (0.5, 0.5, 0), (0, 0.5, 0),
                (0, 0, 0.5), (0.5, 0, 0.5), (0, 0.5, 0.5)]
    elif family in ("C3D6", "C3D15"):
        base = [(0, 0, 0), (1, 0, 0), (0, 1, 0),
                (0, 0, 1), (1, 0, 1), (0, 1, 1)]
    else:
        # cuboid corners, then Abaqus-order midside nodes of a 20-node hex
        base = [(0, 0, 0), (1, 0, 0), (1, 1, 0), (0, 1, 0),
                (0, 0, 1), (1, 0, 1), (1, 1, 1), (0, 1, 1),
                (0.5, 0, 0), (1, 0.5, 0), (0.5, 1, 0), (0, 0.5, 0),
                (0.5, 0, 1), (1, 0.5, 1), (0.5, 1, 1), (0, 0.5, 1),
                (0, 0, 0.5), (1, 0, 0.5), (1, 1, 0.5), (0, 1, 0.5)]
        if family == "C3D27":
            base += [(0.5, 0.5, 0), (0.5, 0.5, 1), (0.5, 0, 0.5),
                     (1, 0.5, 0.5), (0.5, 1, 0.5), (0, 0.5, 0.5),
                     (0.5, 0.5, 0.5)]
    while len(base) < count:
        base.append((0.5 * len(base) / count, 0.25, 0.75))
    return base[:count]


def make_deck(directory, name, element_type, node_count, section="solid", dim=3):
    """Write a minimal .inp deck with one element and return its path."""
    lines = ["*NODE"]
    for node, coord in enumerate(coordinates(element_type, node_count, dim), 1):
        lines.append(f"{node}," + ",".join(str(c) for c in coord))
    lines.append(f"*ELEMENT, TYPE={element_type}, ELSET=EALL")
    lines.append("1," + ",".join(str(node) for node in range(1, node_count + 1)))
    if section == "beam":
        lines += ["*BEAM SECTION, SECTION=RECT, ELSET=EALL, MATERIAL=M1",
                  "0.1,0.2", "0,0,-1"]
    elif section == "solid":
        lines += ["*SOLID SECTION, ELSET=EALL, MATERIAL=M1", "1."]
    else:
        lines += ["*SHELL SECTION, ELSET=EALL, MATERIAL=M1", "1."]
    lines += ["*MATERIAL, NAME=M1", "*DENSITY", "1e-9", "*ELASTIC", "1e5,0.3"]
    deck = directory / f"{name}.inp"
    deck.write_text("\n".join(lines) + "\n")
    return deck


def convert(directory, name, element_type, node_count, section="solid", dim=None):
    if dim is None:
        dim = 2 if element_type.upper() in (
            inp2rad.TWO_D_TRIANGLES | inp2rad.TWO_D_QUADS) else 3
    deck = make_deck(directory, name, element_type, node_count, section, dim)
    out = io.StringIO()
    with contextlib.redirect_stdout(out):
        success = inp2rad.start(str(deck))
    rad = (directory / f"{name}_0000.rad").read_text()
    return success, rad, out.getvalue()


def block_after(rad, keyword):
    """Return the first four lines of the element block beginning with keyword."""
    lines = rad.splitlines()
    start = next(i for i, line in enumerate(lines) if line.startswith(keyword))
    return lines[start:start + 4]


# (Abaqus type, nodes, section, Radioss keyword, first connectivity line)
# The first line contains the element id followed by the first nodes.
ELEMENT_CASES = [
    # 3-noded shells
    ("S3", 3, "shell", "/SH3N", ["1", "1", "2", "3"]),
    ("S3R", 3, "shell", "/SH3N", ["1", "1", "2", "3"]),
    ("M3D3", 3, "shell", "/SH3N", ["1", "1", "2", "3"]),
    ("R3D3", 3, "shell", "/SH3N", ["1", "1", "2", "3"]),
    ("SFM3D3", 3, "shell", "/SH3N", ["1", "1", "2", "3"]),
    # 4-noded shells
    ("S4", 4, "shell", "/SHELL", ["1", "1", "2", "3", "4"]),
    ("S4R", 4, "shell", "/SHELL", ["1", "1", "2", "3", "4"]),
    ("S4RT", 4, "shell", "/SHELL", ["1", "1", "2", "3", "4"]),
    ("S4RSW", 4, "shell", "/SHELL", ["1", "1", "2", "3", "4"]),
    ("M3D4", 4, "shell", "/SHELL", ["1", "1", "2", "3", "4"]),
    ("M3D4R", 4, "shell", "/SHELL", ["1", "1", "2", "3", "4"]),
    ("R3D4", 4, "shell", "/SHELL", ["1", "1", "2", "3", "4"]),
    ("SFM3D4R", 4, "shell", "/SHELL", ["1", "1", "2", "3", "4"]),
    # quadratic shells (degraded to the linear Radioss equivalents)
    ("S6", 6, "shell", "/SH3N", ["1", "1", "2", "3"]),
    ("S6R", 6, "shell", "/SH3N", ["1", "1", "2", "3"]),
    ("S8", 8, "shell", "/SHELL", ["1", "1", "2", "3", "4"]),
    ("S8R", 8, "shell", "/SHELL", ["1", "1", "2", "3", "4"]),
    ("S8RT", 8, "shell", "/SHELL", ["1", "1", "2", "3", "4"]),
    # tetrahedra
    ("C3D4", 4, "solid", "/TETRA4", ["1", "1", "3", "2", "4"]),
    ("DC3D4", 4, "solid", "/TETRA4", ["1", "1", "3", "2", "4"]),
    ("C3D10", 10, "solid", "/TETRA10", ["1"]),
    ("C3D10M", 10, "solid", "/TETRA10", ["1"]),
    ("DC3D10", 10, "solid", "/TETRA10", ["1"]),
    # prisms (degenerate BRICK)
    ("C3D6", 6, "solid", "/BRICK", ["1", "1", "2", "3", "3", "4", "5", "6", "6"]),
    ("DC3D6", 6, "solid", "/BRICK", ["1", "1", "2", "3", "3", "4", "5", "6", "6"]),
    ("SC6R", 6, "solid", "/BRICK", ["1", "1", "2", "3", "3", "4", "5", "6", "6"]),
    ("COH3D6", 6, "solid", "/BRICK", ["1", "1", "2", "3", "3", "4", "5", "6", "6"]),
    ("C3D15", 15, "solid", "/BRICK", ["1", "1", "2", "3", "3", "4", "5", "6", "6"]),
    ("C3D15V", 15, "solid", "/BRICK", ["1", "1", "2", "3", "3", "4", "5", "6", "6"]),
    # hexahedra
    ("C3D8", 8, "solid", "/BRICK", ["1", "1", "2", "3", "4", "5", "6", "7", "8"]),
    ("C3D8R", 8, "solid", "/BRICK", ["1", "1", "2", "3", "4", "5", "6", "7", "8"]),
    ("C3D8I", 8, "solid", "/BRICK", ["1", "1", "2", "3", "4", "5", "6", "7", "8"]),
    ("DC3D8", 8, "solid", "/BRICK", ["1", "1", "2", "3", "4", "5", "6", "7", "8"]),
    ("SC8R", 8, "solid", "/BRICK", ["1", "1", "2", "3", "4", "5", "6", "7", "8"]),
    ("COH3D8", 8, "solid", "/BRICK", ["1", "1", "2", "3", "4", "5", "6", "7", "8"]),
    ("C3D20", 20, "solid", "/BRIC20", ["1", "1", "2", "3", "4", "5", "6", "7", "8"]),
    ("C3D20R", 20, "solid", "/BRIC20", ["1", "1", "2", "3", "4", "5", "6", "7", "8"]),
    ("DC3D20", 20, "solid", "/BRIC20", ["1", "1", "2", "3", "4", "5", "6", "7", "8"]),
    ("C3D27", 27, "solid", "/BRIC20", ["1", "1", "2", "3", "4", "5", "6", "7", "8"]),
    ("C3D27R", 27, "solid", "/BRIC20", ["1", "1", "2", "3", "4", "5", "6", "7", "8"]),
    # single-segment beams
    ("B31", 2, "beam", "/BEAM", ["1", "1", "2", "0", "0", "-1"]),
    ("B32", 3, "beam", "/BEAM", ["1", "1", "3", "0", "0", "-1"]),
    # 2-D continuum elements
    ("CPS3", 3, "solid", "/TRIA", ["1", "1", "2", "3"]),
    ("CPE3", 3, "solid", "/TRIA", ["1", "1", "2", "3"]),
    ("CAX3", 3, "solid", "/TRIA", ["1", "1", "2", "3"]),
    ("CPS4", 4, "solid", "/QUAD", ["1", "1", "2", "3", "4"]),
    ("CPE4R", 4, "solid", "/QUAD", ["1", "1", "2", "3", "4"]),
    ("CAX4", 4, "solid", "/QUAD", ["1", "1", "2", "3", "4"]),
    ("CPS8", 8, "solid", "/QUAD", ["1", "1", "2", "3", "4"]),
]


class AllElementFamilies(unittest.TestCase):
    def test_every_supported_type_converts(self):
        for element_type, nodes, section, keyword, fields in ELEMENT_CASES:
            with self.subTest(element_type=element_type), \
                    tempfile.TemporaryDirectory() as tmp:
                success, rad, log = convert(
                    pathlib.Path(tmp), element_type.lower(), element_type,
                    nodes, section)
                self.assertTrue(success, f"conversion failed for {element_type}")
                self.assertNotIn("Unknown element type", log)
                block = block_after(rad, keyword + "/")
                self.assertEqual(block[1].split(), fields)


class ElementNodeCounts(unittest.TestCase):
    def test_reader_counts_match_aliases(self):
        for element_type, nodes, _, _, _ in ELEMENT_CASES:
            with self.subTest(element_type=element_type):
                self.assertEqual(inp2rad.element_node_count(element_type), nodes)

    def test_unknown_type(self):
        self.assertEqual(inp2rad.element_node_count("NOT_AN_ELEMENT"), 0)

    def test_unknown_type_does_not_block_in_batch(self):
        with mock.patch("sys.stdin", io.StringIO()):
            elements, _ = inp2rad.process_element_block(
                ["1,2,3"], "NOT_AN_ELEMENT", 0)
        self.assertEqual(elements, [])

    def test_reader_uses_shared_table(self):
        lines = ["1," + ",".join(str(n) for n in range(1, 21))]
        elements, _ = inp2rad.process_element_block(lines, "C3D20", 0)
        self.assertEqual(elements[0]["nodes"][-1], "20")


class HigherOrderSolids(unittest.TestCase):
    def test_c3d20_midside_remap(self):
        with tempfile.TemporaryDirectory() as tmp:
            success, rad, _ = convert(
                pathlib.Path(tmp), "hex20", "C3D20", 20)
            self.assertTrue(success)
            block = block_after(rad, "/BRIC20/")
            self.assertEqual(block[2].split(),
                             ["9", "10", "11", "12", "17", "18", "19", "20"])
            self.assertEqual(block[3].split(), ["13", "14", "15", "16"])

    def test_c3d27_drops_extra_nodes(self):
        with tempfile.TemporaryDirectory() as tmp:
            success, rad, log = convert(
                pathlib.Path(tmp), "hex27", "C3D27", 27)
            self.assertTrue(success)
            self.assertIn("/BRIC20/", rad)
            self.assertIn("face and centre nodes are dropped", log)
            block = block_after(rad, "/BRIC20/")
            self.assertEqual(block[2].split(),
                             ["9", "10", "11", "12", "17", "18", "19", "20"])
            self.assertEqual(block[3].split(), ["13", "14", "15", "16"])

    def test_c3d10_node_order(self):
        with tempfile.TemporaryDirectory() as tmp:
            _, rad, _ = convert(pathlib.Path(tmp), "tet10", "C3D10", 10)
            block = block_after(rad, "/TETRA10/")
            self.assertEqual(block[1].split(), ["1"])
            self.assertEqual(block[2].split(),
                             ["1", "3", "2", "4", "7", "6", "5", "8", "10", "9"])

    def test_quadratic_solid_sets_isolid16(self):
        with tempfile.TemporaryDirectory() as tmp:
            _, rad, _ = convert(pathlib.Path(tmp), "hex20b", "C3D20", 20)
            prop_line = next(line for line in rad.splitlines()
                             if line.strip().startswith("16")
                             and "-1" in line)
            self.assertEqual(prop_line.split()[:2], ["16", "-1"])


class AnalysisType(unittest.TestCase):
    def test_axisymmetric_wins_when_mixed_with_plane_elements(self):
        with tempfile.TemporaryDirectory() as tmp:
            directory = pathlib.Path(tmp)
            lines = ["*NODE"]
            lines += [f"{i},{i % 2},{i // 2}" for i in range(1, 9)]
            lines += ["*ELEMENT,TYPE=CPS4,ELSET=A", "1,1,2,4,3",
                      "*ELEMENT,TYPE=CAX4,ELSET=B", "2,5,6,8,7",
                      "*SOLID SECTION,ELSET=A,MATERIAL=M1", "1.",
                      "*SOLID SECTION,ELSET=B,MATERIAL=M1", "1.",
                      "*MATERIAL,NAME=M1", "*DENSITY", "1e-9",
                      "*ELASTIC", "1e5,0.3"]
            deck = directory / "mixed.inp"
            deck.write_text("\n".join(lines) + "\n")
            with contextlib.redirect_stdout(io.StringIO()):
                self.assertTrue(inp2rad.start(str(deck)))
            rad = (directory / "mixed_0000.rad").read_text().splitlines()
            index = rad.index("/ANALY")
            self.assertEqual(rad[index + 1].split()[0], "1")


class QuadraticSurfaceSegments(unittest.TestCase):
    def test_c3d20_faces_use_corner_nodes(self):
        elements = {"C3D20": [{
            "elements": [{"element_id": "1",
                          "nodes": [str(i) for i in range(1, 21)]}],
        }]}
        segments = inp2rad.convert_segments(elements)["1"]
        self.assertEqual(segments["s1"], ["1", "4", "3", "2"])
        self.assertEqual(segments["s2"], ["8", "5", "6", "7"])
        self.assertEqual(segments["s6"], ["4", "1", "5", "8"])

    def test_aliases_reach_the_same_faces(self):
        for element_type in ("C3D20R", "C3D27", "SC8R"):
            with self.subTest(element_type=element_type):
                elements = {element_type: [{
                    "elements": [{"element_id": "1",
                                  "nodes": [str(i) for i in range(1, 21)]}],
                }]}
                self.assertIn("1", inp2rad.convert_segments(elements))


class Regressions(unittest.TestCase):
    def test_linear_solids_keep_their_connectivity(self):
        for element_type, fields in (
            ("C3D4", ["1", "1", "3", "2", "4"]),
            ("C3D6", ["1", "1", "2", "3", "3", "4", "5", "6", "6"]),
            ("C3D8", ["1", "1", "2", "3", "4", "5", "6", "7", "8"]),
            ("C3D10", ["1"]),
        ):
            with self.subTest(element_type=element_type), \
                    tempfile.TemporaryDirectory() as tmp:
                _, rad, _ = convert(
                    pathlib.Path(tmp), "lin_" + element_type.lower(),
                    element_type, inp2rad.element_node_count(element_type))
                keyword = "/TETRA4/" if element_type == "C3D4" else (
                    "/TETRA10/" if element_type == "C3D10" else "/BRICK/")
                self.assertEqual(block_after(rad, keyword)[1].split(), fields)


class SolverReadability(unittest.TestCase):
    """Check that OpenCourant actually reads the generated decks."""

    STARTER = os.environ.get(
        "OPENCOURANT_STARTER",
        "/home/fernando/Build/OpenCourant/OpenCourant/exec/starter_linux64_gf")
    ROOT = os.environ.get(
        "OPENCOURANT_PATH", "/home/fernando/Build/OpenCourant/OpenCourant")
    ENGINE = os.environ.get(
        "OPENCOURANT_ENGINE",
        "/home/fernando/Build/OpenCourant/OpenCourant/exec/engine_linux64_gf")

    def solver_env(self):
        env = os.environ.copy()
        env["RAD_CFG_PATH"] = os.path.join(self.ROOT, "hm_cfg_files")
        libs = [os.path.join(self.ROOT, "extlib", "h3d", "lib", "linux64"),
                os.path.join(self.ROOT, "extlib", "hm_reader", "linux64")]
        env["LD_LIBRARY_PATH"] = ":".join(
            libs + [env.get("LD_LIBRARY_PATH", "")])
        return env

    @unittest.skipUnless(os.path.exists(STARTER), "OpenCourant starter not available")
    def test_starter_accepts_all_element_types(self):
        for element_type, nodes, section, _, _ in ELEMENT_CASES:
            if element_type.upper() in inp2rad.TWO_D_TRIANGLES:
                # Radioss /TRIA accepts only LAW151 (multifluid), so an
                # elastic *BEAM SECTION/ELASTIC triangle deck is rejected by
                # the starter for reasons unrelated to the conversion.
                continue
            with self.subTest(element_type=element_type), \
                    tempfile.TemporaryDirectory() as tmp:
                directory = pathlib.Path(tmp)
                success, _, _ = convert(
                    directory, element_type.lower(), element_type, nodes, section)
                self.assertTrue(success, f"conversion failed for {element_type}")
                rad = next(directory.glob("*_0000.rad"))
                result = subprocess.run(
                    [self.STARTER, "-i", rad.name, "-np", "1"],
                    cwd=directory, env=self.solver_env(),
                    capture_output=True, text=True)
                log = result.stdout + result.stderr
                self.assertEqual(result.returncode, 0, log[-800:])
                self.assertIn("0 ERROR(S)", log, log[-800:])

    @unittest.skipUnless(
        os.path.exists(STARTER) and os.path.exists(ENGINE),
        "OpenCourant starter/engine not available")
    def test_engine_runs_beam_and_2d_decks(self):
        for element_type, nodes, section in (
            ("B31", 2, "beam"), ("CPS4", 4, "solid")):
            with self.subTest(element_type=element_type), \
                    tempfile.TemporaryDirectory() as tmp:
                directory = pathlib.Path(tmp)
                convert(directory, element_type.lower(), element_type,
                        nodes, section)
                starter_rad = next(directory.glob("*_0000.rad"))
                starter = subprocess.run(
                    [self.STARTER, "-i", starter_rad.name, "-np", "1"],
                    cwd=directory, env=self.solver_env(),
                    capture_output=True, text=True)
                self.assertEqual(starter.returncode, 0, starter.stdout[-800:])
                engine_rad = next(directory.glob("*_0001.rad"))
                engine = subprocess.run(
                    [self.ENGINE, "-nt", "1", "-i", engine_rad.name],
                    cwd=directory, env=self.solver_env(),
                    capture_output=True, text=True)
                self.assertEqual(engine.returncode, 0, engine.stdout[-800:])
                self.assertIn("NORMAL TERMINATION", engine.stdout + engine.stderr)


if __name__ == "__main__":
    unittest.main()
