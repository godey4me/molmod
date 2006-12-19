# MolMod is a collection of molecular modelling tools for python.
# Copyright (C) 2005 Toon Verstraelen
#
# This file is part of MolMod.
#
# MolMod is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.
#
# --

from molmod.data import periodic
from molmod.units import from_angstrom, to_angstrom

from StringIO import StringIO

import numpy, math


__all__ = ["Molecule"]


class Molecule:
    """
    A Molecule instance describes a molecule in the following representation:
    - cartesian coordinates
    """

    def __init__(self, numbers=None, coordinates=None):
        self.numbers = numbers
        self.coordinates = coordinates

    def dump_atoms(self, stream):
        for number, coordinate in zip(self.numbers, to_angstrom(self.coordinates)):
            atom_info = periodic[number]
            if atom_info is None:
                symbol = 'X'
            else:
                symbol = atom_info.symbol
            print >> stream, "% 2s % 12.6f % 12.6f % 12.6f" % (
                symbol,
                coordinate[0],
                coordinate[1],
                coordinate[2]
            )

    def dumps_atoms(self):
        sio = StringIO()
        self.dump_atoms(sio)
        result = sio.getvalue()
        sio.close()
        return result

    def dump(self, stream):
        print >> stream, "%5i" % len(self.numbers)
        print >> stream
        self.dump_atoms(stream)

    def write_to_file(self, filename):
        f = file(filename, 'w')
        self.dump(f)
        f.close()

    def normalize(self):
        """
        Bring the molecule in a normalized frame. This only works if the
        first three atoms are not colinear which is the case for general
        molecules.
        """
        # first translate the first atom to the center
        self.coordinates -= self.coordinates[0].copy()
        # then rotate the molecule so that the second atom lies on the positive x-axis
        # and the third atom lies in the xy-plane with positive y.
        new_x = self.coordinates[1].copy()
        new_x /= math.sqrt(numpy.dot(new_x, new_x))
        third = self.coordinates[2].copy()
        new_z = numpy.array([
            new_x[1]*third[2]-third[1]*new_x[2],
            new_x[2]*third[0]-third[2]*new_x[0],
            new_x[0]*third[1]-third[0]*new_x[1]
        ])
        new_z /= math.sqrt(numpy.dot(new_z, new_z))
        new_y = numpy.array([
            new_z[1]*new_x[2]-new_x[1]*new_z[2],
            new_z[2]*new_x[0]-new_x[2]*new_z[0],
            new_z[0]*new_x[1]-new_x[0]*new_z[1]
        ])
        rotation = numpy.transpose(numpy.array([new_x, new_y, new_z]))
        self.coordinates = numpy.dot(self.coordinates, rotation)

    def bounding_box(self, margin=0.0):
        bbox_low = self.coordinates.min(axis=0) - margin
        bbox_high = self.coordinates.max(axis=0) + margin
        return bbox_low, bbox_high

    def surrounding_grid(self, grid_margin, grid_spacing):
        bbox_low, bbox_high = self.bounding_box(grid_margin)
        bbox_size = bbox_high - bbox_low
        bbox_num = numpy.array(numpy.floor(bbox_size/grid_spacing), int)
        bbox_cor = 0.5*(bbox_size - bbox_num*grid_spacing)
        bbox_low += bbox_cor
        bbox_high -= bbox_cor
        return (
            bbox_low,
            bbox_num[0],
            numpy.array([grid_spacing, 0, 0], float),
            bbox_num[1],
            numpy.array([0, grid_spacing, 0], float),
            bbox_num[2],
            numpy.array([0, 0, grid_spacing], float)
        )
