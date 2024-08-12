#SETTING UP BW
#importing individual brightway packages directly
import bw2analyzer as ba
import bw2calc as bc
import bw2data as bd
import bw2io as bi
#importing most important data science packages —› those are suggested by brightway getting started protocol (https://learn.brightway.dev/en/latest/content/notebooks/BW25_for_beginners.html#section1)
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import os
#
#WORK WITH A PROJECT
#
#creating a new project
name = "testing_240812" #when you change the name here then the project is directly added to the list of the projects
bd.projects.set_current(name)
#listing all available projects and checking if "name" was added to the project list
#print(bd.projects)
#
#DATABASES
#setting up database

#listing all available databases in the project
#print(bd.databases)


