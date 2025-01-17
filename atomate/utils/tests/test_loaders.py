import os
import unittest

from monty.serialization import loadfn
from pymatgen.util.testing import PymatgenTest

from atomate.utils.utils import get_wf_from_spec_dict

# TODO: @computron - move this test if you also move the loader code -computron

module_dir = os.path.dirname(os.path.abspath(__file__))


class FuncTest(PymatgenTest):
    def setUp(self):
        self.structure = PymatgenTest.get_structure("Si")

    def test_get_wf_from_spec_dict(self):
        d = loadfn(os.path.join(module_dir, "spec.yaml"))
        wf = get_wf_from_spec_dict(self.structure, d)
        self.assertEqual(len(wf.fws), 4)
        for f in wf.fws:
            self.assertEqual(f.tasks[-1]["db_file"], "db.json")

        self.assertEqual(sorted(len(v) for v in wf.links.values()), [0, 0, 1, 2])

        self.assertEqual(wf.name, "Si:band structure")
        d = loadfn(os.path.join(module_dir, "badspec.yaml"))

        self.assertRaises(ImportError, get_wf_from_spec_dict, self.structure, d)

    def test_multi_parent(self):
        d = loadfn(os.path.join(module_dir, "spec_multi.yaml"))
        wf = get_wf_from_spec_dict(self.structure, d)
        self.assertEqual(len(wf.fws), 3)
        self.assertEqual(sorted(len(v) for v in wf.links.values()), [0, 1, 1])


if __name__ == "__main__":
    unittest.main()
