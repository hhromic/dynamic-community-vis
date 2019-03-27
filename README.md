# Dynamic Community Visualisation (DCV)

This is a visualisation tool for tracking the life cycle of communities over time in a dynamic network, where each community is characterised by a series of significant evolutionary events.
The DCV is capable of visualising the development of these events at different points in time using browsable timelines.
Specifically, it can visualise the birth, death, split, merge, contraction, expansion and any user-defined attribute change (e.g. topics) as evolutionary events for sets of dynamic communities.

This tool is based on an established community tracking model that leverages a community-matching strategy for efficiently identifying and tracking dynamic communities:

> D.Greene, D.Doyle, and P.Cunningham, "Tracking the evolution of communities in dynamic
> social networks," in Proc. International Conference on Advances in Social Networks
> Analysis and Mining (ASONAM'10), 2010.
> Repository: <https://github.com/derekgreene/dynamic-community>

For further details on our visualisation approach and its applications, please consult the following publication:

> H.Hromic, C.Hayes, "Visualising the Evolution of Dynamic Communities in Social
> Networks using Timelines" in Proc. ECML/PKDD Workshop on Advanced Analytics and
> Learning on Temporal Data (AALTD'18), 2018.

## Installation

This tool needs no particular installation. However, to run the HTML user interface, you will need an HTTP server to serve the files in the `public` folder of this repository.

As a suggestion, you can use [Node.js](https://nodejs.org/) and the modules:

* [http-server](https://npmjs.com/package/http-server): a command-line http server
* [pm2](https://npmjs.com/package/pm2): P(rocess) M(anager) 2 Runtime Edition

to get started quickly using the included `dcv-app.json` pm2 declaration file.

Furthermore, to run the `tracker2vis.py` script, you will need Python 3.

## Usage

The Dynamic Community Visualisation requires three data files in the `public/data` folder of this repository for each of your dynamic communities datasets:

* `DATASET_NAME.steps.json`: static steps description
* `DATASET_NAME.timeline.json`: dynamic communities timeline
* `DATASET_NAME.events.json`: computed evolutionary events

Once you have your files prepared, place them in `public/data` and edit the `public/js/datasets.js` file accordingly.
After reloading the user interface, your dataset should appear in the drop-down box for selection.

To generate the files for your data, follow the instructions below. Example data can be found in the `example` folder of this repository.

### Compute Dynamic Communities Timeline

First, you need to obtain static communities from your data using any community detection algorithm and time granularity you deem suitable for your purposes.

The input static step files `STATIC_STEP_NUMBER.comm` use the format (from Greene et al.):

    C1_U1 C1_U2 C1_U3 ...
    C2_U1 C2_U2 ...
    ...

With one community `C` per line and its member users `U` separated by spaces.

The files should be named with integer numbers of fixed length to ensure they are processed in order. For example: `00001.comm`, `00002.comm`, `00003.comm`, etc.

Then, using the algorithm from Greene et al., generate the `example.timeline` file from your static step files using this command:

    tracker *.comm -o example

The output `example.timeline` file from the tracker should look like this:

    M1:1=1,2=1,3=1,5=1,6=1,7=1,8=1
    M2:2=2,3=3,4=2,5=4,6=3,7=2
    M3:3=2,4=1,5=2,6=2
    M4:3=2,4=1,5=3,6=3,7=2

The format of the above timeline (from Greene et al.) is:

    DYN_C1:STATIC_STEP_NUMBER=COMMUNITY_NUMBER_IN_STATIC_STEP_NUMBER,...
    DYN_C2:STATIC_STEP_NUMBER=COMMUNITY_NUMBER_IN_STATIC_STEP_NUMBER,...
    ...

### Convert Static Steps to JSON

For the visualisation you also must generate a `example.steps.json` JSON file from your input static step files with the following structure/schema:

    {
      "steps": {
        "STATIC_STEP_NUMBER": {
          "time": EPOCH_TIMESTAMP_IN_SECONDS,
          "communities": {
            "COMMUNITY_NUMBER_IN_STATIC_STEP_NUMBER": {
              "data": ARBITRARY_OBJECT,
              "users": ["U1", "U2", "U3", ...]
            },
            ...
          }
        },
        ...
      },
      "data_keys": ["KEY_IN_DATA_OBJ", "KEY_IN_DATA_OBJ", ... ]
    }

This file provides information about the real times used in your static steps and the community meta-data to be visualised by the tool.

### Compute Evolutionary Events and Convert Dynamic Timeline to JSON

To build the evolutionary events for visualisation. Run this script to generate the `example.timeline.json` and `example.events.json` files:

    python/tracker2vis.py \
        --timeline example.timeline \
        --output example.timeline.json \
        --events example.events.json

This invocation assumes that the original static step files (`*.comm`) are in the current directory.
If this is not the case, you can optionally provide the directory name containing these files using the argument `--steps-dir <DIR>`.

The output `example.timeline.json` file should look similar to this:

    [
      {
        "data": [
          {"step": 1, "community": 1},
          {"step": 2, "community": 1},
          {"step": 3, "community": 1},
          {"step": 5, "community": 1},
          {"step": 6, "community": 1},
          {"step": 7, "community": 1},
          {"step": 8, "community": 1}
        ],
        "name": "M1"
      }
      ...
    ]

And the second output `example.events.json` file should be like this:

    {
      "contractions": [
        {"source": {"step": 4, "name": "M3"}, "reduction": 1, "target": {"step": 5, "name": "M3"}},
        ...
      ],
      "splits": [
        {"source": {"step": 4, "name": "M3"}, "target": {"step": 5, "name": "M4"}},
        ...
      ],
      "deaths": [
        {"step": 8, "name": "M1"},
        {"step": 7, "name": "M2"},
        {"step": 6, "name": "M3"},
        {"step": 5, "name": "M4"},
        ...
      ],
      "merges": [
        {"source": {"step": 5, "name": "M4"}, "target": {"step": 6, "name": "M2"}},
        ...
      ],
      "births": [
        {"step": 1, "name": "M1"},
        {"step": 2, "name": "M2"},
        {"step": 3, "name": "M3"},
        {"step": 5, "name": "M4"},
        ...
      ],
      "expansions": [
        {"source": {"step": 5, "name": "M2"}, "growth": 0.75, "target": {"step": 6, "name": "M2"}},
        ...
      ],
      "intermittents": [
        {"step": 4, "name": "M1"},
        ...
      ]
    }

These two files provide information about the dynamic timelines and the community evolutionary events in them.

## License

This software is under the **Apache License 2.0**.

    Licensed under the Apache License, Version 2.0 (the "License");
    you may not use this file except in compliance with the License.
    You may obtain a copy of the License at

        http://www.apache.org/licenses/LICENSE-2.0

    Unless required by applicable law or agreed to in writing, software
    distributed under the License is distributed on an "AS IS" BASIS,
    WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
    See the License for the specific language governing permissions and
    limitations under the License.

