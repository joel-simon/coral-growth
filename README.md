# coral_growth

A research project simulating the evolution of virtual corals. Corals are grown in a simulated underwater environment and evolved with a genetic-algorithm. Morphogens, signaling, memory and other biologically motived capacities enable a multipurpose biomemetic form optimization engine.

The coral is modelled as a 3d mesh with a neural net that is evaluated across each node. Each node detects its light, water and curvature and may grow along its normal vector. This neural network is evolved with the NEAT genetic algorithm.


## INSTALL
Requires python3, cython, numpy, pygame/pyopengl (for viewing), [pykdtree](https://github.com/storpipfugl/pykdtree), [MultiNEAT](https://github.com/peter-ch/MultiNEAT).

Requires my helf-edge mesh library [cymesh](https://github.com/joel-simon/cymesh)

```
https://github.com/joel-simon/coral-growth
cd coral-growth
python setup.py build_ext -i

cd bin/

./evolve --out output/ --gens 100 --cores 4

```

There are several scripts in the bin folder.
### evolve
The main evolve script. Any parameter present in the parameters.py or MultiNEAT parameter can be optionally sent as well.

```
usage: evolve [-h] [--gens GENS] [--out OUT] [--cores CORES] [--method METHOD]

optional arguments:
  -h, --help       show this help message and exit
  --gens GENS      Number of generations.
  --out OUT        Output directory.
  --cores CORES    Number of cores.
  --method METHOD  'neat', 'novelty' or 'local'

```

For example:

`python3.4 evolve --cores 4 --gens 800 --out ../../output/ --light_amount 0.5 --collection_radius 5 —max_growth .5 --C 1.0 --max_volume 100.0 --gradient_height 4.0 --method novelty
`

### rand

A rand script for visualizing the growth of a random coral. Useful for debugging. Useful for profilling if run with --show 0.

```
usage: rand [-h] [--steps STEPS] [--show SHOW] [--net NET]

optional arguments:
  -h, --help     show this help message and exit
  --steps STEPS  Num Steps.
  --show SHOW    Display output.
  --net NET      The network has random output instead of a random network.
```

### show
Visualize the growth of a a coral. Must be passed the base output directory of a coral.

```
usage: show [-h] [--width WIDTH] [--height HEIGHT] [--all ALL]
            [input [input ...]]

positional arguments:
  input

optional arguments:
  -h, --help       show this help message and exit
  --width WIDTH    Screen width.
  --height HEIGHT  Screen height.
  --all ALL        Show all growth steps or just the last.
```


### simulate
Re simualtes the growth of a coral using the genone and traits file. Must be passed the base output of a run (not coral).

```
usage: simulate [-h] [--max_nodes MAX_POLYPS] [--max_steps MAX_STEPS]
                   path generation

positional arguments:
  path
  generation

optional arguments:
  -h, --help            show this help message and exit
  --max_nodes MAX_POLYPS
                        Generations.
  --max_steps MAX_STEPS
                        Output dir.
```
