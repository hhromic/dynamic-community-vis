#!/usr/bin/env python3
# Hugo Hromic <hugo.hromic@insight-centre.org>
#
# Based on the following paper:
# Greene, Derek, Donal Doyle, and Padraig Cunningham. "Tracking the evolution of
# communities in dynamic social networks." Advances in social networks analysis and
# mining (ASONAM), 2010 international conference on. IEEE, 2010.
# http://derekgreene.com/wp-content/papercite-data/pdf/greene10tracking.pdf
#
# Discoverable timeline events:
# split, merge, birth, death, intermittence, expansion, contraction

"""Dynamic timeline helpers."""

import json
from itertools import combinations, zip_longest

# pylint: disable=too-few-public-methods
class TimelineStep(object):
    """Represents a dynamic community timeline step."""

    def __init__(self, raw_str):
        number, community = raw_str.split("=")
        self.number = int(number)
        self.community = int(community)

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return self.__dict__ == other.__dict__
        return NotImplemented

    def __ne__(self, other):
        if isinstance(other, self.__class__):
            return not self.__eq__(other)
        return NotImplemented

    def __repr__(self):
        return "{%d=%d}" % (self.number, self.community)

class DynamicCommunity(object):
    """Represents a dynamic community in the timeline."""

    def __init__(self, raw_str):
        self.name, raw_steps = raw_str.split(":")
        self.steps = [TimelineStep(raw_step) for raw_step in raw_steps.split(",")]

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return self.__dict__ == other.__dict__
        return NotImplemented

    def __ne__(self, other):
        if isinstance(other, self.__class__):
            return not self.__eq__(other)
        return NotImplemented

    def __repr__(self):
        return "{'%s':%s}" % (self.name, self.steps)

    def remove_until(self, step):
        """Remove all steps in this dynamic community until the given step (exclusive)."""
        self.steps[:] = filter(lambda s: s.number >= step.number, self.steps)

    def remove_after(self, step):
        """Remove all steps in this dynamic community after the given step (exclusive)."""
        self.steps[:] = filter(lambda s: s.number <= step.number, self.steps)

class TimelineEvents(list):
    """Represents timeline events."""

    def correct_target(self, duplicates):
        """Correct event targets using a list of removed duplicate dynamic communities."""
        for d_i, d_j in duplicates:
            for e in self:  # pylint: disable=invalid-name
                if e["target"]["name"] == d_j.name:
                    e["target"]["name"] = d_i.name

    def remove_orphans(self, timeline):
        """Remove events whose source and/or target no longer exists in a timeline."""
        tl_dict = {d.name: set([s.number for s in d.steps]) for d in timeline}
        self[:] = filter(lambda e: e["source"]["step"] in tl_dict[e["source"]["name"]], self)
        self[:] = filter(lambda e: e["target"]["step"] in tl_dict[e["target"]["name"]], self)

class Timeline(list):
    """Represents a dynamic communities timeline."""

    def __init__(self, reader):
        super().__init__()
        with reader:
            self[:] = [DynamicCommunity(line.strip()) for line in reader]

    def deduplicate(self):
        """Remove duplicate dynamic communities in the timeline, returning found duplicates."""
        dups = [(d_i, d_j) for d_i, d_j in combinations(self, r=2) if d_i.steps == d_j.steps]
        dup_names = set([d_j.name for _, d_j in dups])
        self[:] = filter(lambda d: d.name not in dup_names, self)
        return dups

    def find_splits(self):
        """Find split events, removing the shared steps in the branching (regularize).
           A branching occurs with the creation of an additional dynamic community
           D_j that shares the timeline of D_i up to time t-1, but has a distinct
           timeline from time t onwards."""
        splits = TimelineEvents()
        for d_i, d_j in combinations(self, r=2):
            if d_i.steps[0] == d_j.steps[0]:
                s_prev = None
                for s_i, s_j in zip_longest(d_i.steps, d_j.steps):
                    if s_i and s_j and s_i != s_j:
                        splits.append({
                            "source": {"name": d_i.name, "step": s_prev.number},
                            "target": {"name": d_j.name, "step": s_j.number},
                        })
                        d_j.remove_until(s_j)
                        break
                    s_prev = s_i
        duplicates = self.deduplicate()
        splits.correct_target(duplicates)
        return splits

    def find_merges(self):
        """Find merge events, removing the shared steps in the merging (regularize).
           A merge occurs if two distinct dynamic communities (D_i, D_j) observed at
           time t-1 match to a single step community C_ta at time t. The pair subsequently
           share a common timeline starting from C_ta."""
        merges = TimelineEvents()
        for d_i, d_j in combinations(self, r=2):
            if d_i.steps[-1] == d_j.steps[-1]:
                s_prev = None
                for s_i, s_j in zip_longest(reversed(d_i.steps), reversed(d_j.steps)):
                    if s_i and s_j and s_i != s_j:
                        merges.append({
                            "source": {"name": d_j.name, "step": s_j.number},
                            "target": {"name": d_i.name, "step": s_prev.number},
                        })
                        d_j.remove_after(s_j)
                        break
                    s_prev = s_i
        duplicates = self.deduplicate()
        merges.correct_target(duplicates)
        return merges

    def find_births(self):
        """Find birth events in the timeline.
           The emergence of a step community C_tj observed at time t for which
           there is no corresponding dynamic community in D."""
        return TimelineEvents([{"name": d.name, "step": d.steps[0].number} for d in self])

    def find_deaths(self):
        """Find death events in the timeline.
           The dissolution of a dynamic community D_i occurs when it has no longer been
           observed (i.e. there has been no corresponding step community)."""
        return TimelineEvents([{"name": d.name, "step": d.steps[-1].number} for d in self])

    def find_intermittents(self):
        """Find intermittent events in the timeline."""
        return TimelineEvents([{"name": d.name, "step": s_i.number + 1}
                               for d in self for s_i, s_j in zip(d.steps, d.steps[1:])
                               if s_i.number + 1 != s_j.number])

    def find_expansions(self, step_communities, threshold=0.10):
        """Find expansion events in the timeline.
           The expansion or growth of a dynamic community D_i occurs when its corresponding
           step community at time t is significantly larger than the previous front associated
           with D_i (e.g. a growth of > 10%)."""
        expansions = TimelineEvents()
        for d in self:  # pylint: disable=invalid-name
            for s_i, s_j in zip(d.steps, d.steps[1:]):
                c_i = step_communities[s_i.number][s_i.community]
                c_j = step_communities[s_j.number][s_j.community]
                if len(c_j) > len(c_i) and len(c_j) / float(len(c_i)) - 1.0 > threshold:
                    expansions.append({
                        "source": {"name": d.name, "step": s_i.number},
                        "target": {"name": d.name, "step": s_j.number},
                        "growth": len(c_j) / float(len(c_i)) - 1.0,
                    })
        return expansions

    def find_contractions(self, step_communities, threshold=0.10):
        """Find contraction events in the timeline.
           The contraction or reduction of a dynamic community D_i occurs when its corresponding
           step community at time t is significantly smaller than the previous front associated
           with D_i (e.g. a reduction of > 10%)."""
        contractions = []
        for d in self:  # pylint: disable=invalid-name
            for s_i, s_j in zip(d.steps, d.steps[1:]):
                c_i = step_communities[s_i.number][s_i.community]
                c_j = step_communities[s_j.number][s_j.community]
                if len(c_i) > len(c_j) and len(c_i) / float(len(c_j)) - 1.0 > threshold:
                    contractions.append({
                        "source": {"name": d.name, "step": s_i.number},
                        "target": {"name": d.name, "step": s_j.number},
                        "reduction": len(c_i) / float(len(c_j)) - 1.0,
                    })
        return contractions

    def to_vis_json(self, writer):
        """Convert the timeline into a JSON representation for visualisation."""
        with writer:
            writer.write("%s\n" % json.dumps([{
                "name": d.name,
                "data": [{
                    "step": s.number,
                    "community": s.community,
                } for s in d.steps],
            } for d in self], separators=(",", ":")))
