# coding: utf-8

from __future__ import division, print_function, unicode_literals, absolute_import

"""
This module defines functions that generate workflows for bandstructure calculations.
"""

from fireworks import Workflow, LaunchPad

from matmethods.vasp.vasp_powerups import decorate_write_name

from matmethods.vasp.fws import OptimizeFW, StaticFW, NonSCFUniformFW, \
    NonSCFLineFW, LepsFW

from pymatgen import Lattice, IStructure
from monty.json import MontyDecoder


__author__ = 'Anubhav Jain, Kiran Mathew'
__email__ = 'ajain@lbl.gov, kmathew@lbl.gov'


def get_wf_bandstructure(structure, vasp_input_set=None, vasp_cmd="vasp",
                         db_file=None, dielectric=False):
    """
    Return vasp workflow consisting of 4 fireworks:

    Firework 1 : write vasp input set for structural relaxation,
                 run vasp,
                 pass run location,
                 database insertion.

    Firework 2 : copy files from previous run,
                 write vasp input set for static run,
                 run vasp,
                 pass run location
                 database insertion.

    Firework 3 : copy files from previous run,
                 write vasp input set for non self-consistent(constant charge density) run in
                 uniform mode,
                 run vasp,
                 pass run location
                 database insertion.

    Firework 4 : copy files from previous run,
                 write vasp input set for non self-consistent(constant charge density) run in
                 line mode,
                 run vasp,
                 pass run location
                 database insertion.

    Args:
        structure (Structure): input structure to be relaxed.
        vasp_input_set (DictVaspInputSet): vasp input set.
        vasp_cmd (str): command to run
        db_file (str): path to file containing the database credentials.
        dielectric (bool): Whether to add a dielectric task.

    Returns:
        Workflow
     """
    common_kwargs = {"vasp_cmd": vasp_cmd, "db_file": db_file}

    fw1 = OptimizeFW(structure=structure, vasp_input_set=vasp_input_set, **common_kwargs)
    fw2 = StaticFW(structure=structure, copy_vasp_outputs=True, parents=fw1, **common_kwargs)
    fw3 = NonSCFUniformFW(structure=structure, copy_vasp_outputs=True, parents=fw2, **common_kwargs)
    fw4 = NonSCFLineFW(structure=structure, copy_vasp_outputs=True, parents=fw2, **common_kwargs)

    # line mode (run in parallel to uniform)

    wf = [fw1, fw2, fw3, fw4]

    if dielectric:
        wf.append(LepsFW(structure=structure, copy_vasp_outputs=True, parents=fw2, **common_kwargs))

    return Workflow(wf, name=structure.composition.reduced_formula)


def add_to_lpad(workflow, decorate=False):
    """
    Add the workflow to the launchpad

    Args:
        workflow (Workflow): workflow for db insertion
        decorate (bool): If set an empty file with the name
            "FW--<fw.name>" will be written to the launch directory
    """
    lp = LaunchPad.auto_load()
    workflow = decorate_write_name(workflow) if decorate else workflow
    lp.add_wf(workflow)



def get_wf_from_spec_dict(structure, wfspec):
    fws = []
    for d in wfspec["fireworks"]:
        modname, classname = d["fw"].rsplit(".", 1)
        mod = __import__(modname, globals(), locals(), [classname], 0)
        if hasattr(mod, classname):
            cls_ = getattr(mod, classname)
            kwargs = {k: MontyDecoder().process_decoded(v) for k, v in d.get("params", {}).items()}
            if "parents" in kwargs:
                kwargs["parents"] = fws[kwargs["parents"]]
            fws.append(cls_(structure, **kwargs))
    return Workflow(fws, name=structure.composition.reduced_formula)


if __name__ == "__main__":
    coords = [[0, 0, 0], [0.75, 0.5, 0.75]]
    lattice = Lattice([[3.8401979337, 0.00, 0.00],
                       [1.9200989668, 3.3257101909, 0.00],
                       [0.00, -2.2171384943, 3.1355090603]])
    structure = IStructure(lattice, ["Si"] * 2, coords)
    wf = get_wf_bandstructure(structure)
    #add_to_lpad(wf, decorate=True)
