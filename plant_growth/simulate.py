import os
import time
from plant_growth import constants
from plant_growth.world import World
import MultiNEAT as NEAT

obj_path = os.getcwd()+'/../data/triangulated_sphere_1.obj'

def __export(world, folder, w_i, s):
    out = open(os.path.join(folder, str(w_i), '%i.plant.obj'%s), 'w+')
    world.plants[0].export(out)

def simulate_network(network, world_configs, export_folder=None):
    plants = []

    for w_i, w_config in enumerate(world_configs):
        world = World(w_config)
        world.add_plant(obj_path, network)

        if export_folder:
            os.mkdir(os.path.join(export_folder, str(w_i)))
            __export(world, export_folder, w_i, 0)

        for s in range(constants.SIMULATION_STEPS):
            world.simulation_step()

            if export_folder: __export(world, export_folder, w_i, s+1)

            if not world.plants[0].alive: break

        plants.append(world.plants[0])

    return plants

def simulate_genome(genome, world_configs, export_folder=None):
    network = NEAT.NeuralNetwork()
    genome.BuildPhenotype(network)
    return simulate_network(network, world_configs, export_folder)
