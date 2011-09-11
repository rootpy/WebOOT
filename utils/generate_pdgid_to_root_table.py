#! /usr/bin/env python

import mcviz.utils.svg.texglyph as T
from yaml import safe_dump

result = {}

db = T.read_pythia_particle_db()
for pdgid, label, gd in sorted(db.values()):
    result[pdgid] = T.particle_to_latex(gd, True)
    
print safe_dump(result)
