# plant_growth
A new model for evolving virtual plant species. The plant is modelled as a polygon with a neural net that is evaluated across each node. Each node detects its light, water and curvature and may grow along its normal vector. If a plant attempts to consume more energy than it collects it will die. 

The first batch of grown plants is collected here https://www.youtube.com/playlist?list=PL6nTquhrGRMTVMFlYDQ4BDa7zjwPdlekO

TODO:
* represent plant interior as mesh
* cell differentiation and flower type. Evalaute plants by flower volume.
* plant physics, spring system on mesh with implicit euler method, evalaute for n steps per simulation step
* water grid where water may be exausted locally
* Single world where plants directly compete for light and water. 
