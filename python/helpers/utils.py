#!/usr/bin/env python3
# Hugo Hromic <hugo.hromic@insight-centre.org>

"""Utility helpers."""

import sys
from os import listdir
from os.path import isfile, join

def get_reader(filename):
    """Get a suitable reader given a filename."""
    return sys.stdin if filename is None else open(filename)

def get_writer(filename):
    """Get a suitable writer given a filename."""
    return sys.stdout if filename is None else open(filename, "w")

def read_step_communities(dirname):
    """Read community step files (*.comm) from a directory."""
    steps = {}
    for step, filename in enumerate(sorted(
            [fn for fn in listdir(dirname) if isfile(join(dirname, fn))
             and fn.endswith(".comm")]), start=1):
        with get_reader(join(dirname, filename)) as reader:
            steps[step] = {community: [int(u) for u in users.strip().split(" ")]
                           for community, users in enumerate(reader, start=1)}
    return steps
