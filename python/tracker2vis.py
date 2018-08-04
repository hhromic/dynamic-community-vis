#!/usr/bin/env python3
# Hugo Hromic <hugo.hromic@insight-centre.org>

"""Generate timeline and events in JSON representation for visualisation."""

import json
from argparse import ArgumentParser
from helpers.utils import get_reader, get_writer, read_step_communities
from helpers.timeline import Timeline

def main():
    """Module entry-point."""
    epilog = "You can omit filenames to use standard input/output."
    parser = ArgumentParser(description=__doc__, epilog=epilog)
    parser.add_argument(
        "--timeline", metavar="FILENAME",
        help="filename for the input timeline (in dynamic tracker text format)")
    parser.add_argument(
        "--steps-dir", metavar="DIRECTORY", default="./",
        help="directory with community step files (in dynamic tracker text format)")
    parser.add_argument(
        "--expansion-threshold", metavar="FLOAT", type=float, default=0.10,
        help="growth threshold for detecting expansions (percentual)")
    parser.add_argument(
        "--contraction-threshold", metavar="FLOAT", type=float, default=0.10,
        help="reduction threshold for detecting contractions (percentual)")
    parser.add_argument(
        "--output", metavar="FILENAME",
        help="filename for the output timeline (in JSON format)")
    parser.add_argument(
        "--events", metavar="FILENAME", required=True,
        help="filename for the output timeline events (in JSON format)")
    args = parser.parse_args()

    with get_reader(args.timeline) as reader:
        timeline = Timeline(reader)

    splits = timeline.find_splits()
    merges = timeline.find_merges()
    splits.remove_orphans(timeline)
    births = timeline.find_births()
    deaths = timeline.find_deaths()
    intermittents = timeline.find_intermittents()

    step_communities = read_step_communities(args.steps_dir)
    expansions = timeline.find_expansions(step_communities, args.expansion_threshold)
    contractions = timeline.find_contractions(step_communities, args.contraction_threshold)

    with get_writer(args.output) as writer:
        timeline.to_vis_json(writer)

    with get_writer(args.events) as writer:
        writer.write("%s\n" % json.dumps({
            "splits": splits,
            "births": births,
            "merges": merges,
            "deaths": deaths,
            "intermittents": intermittents,
            "expansions": expansions,
            "contractions": contractions,
        }, separators=(",", ":")))

if __name__ == "__main__":
    main()
