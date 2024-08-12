#SETTING UP BW
#importing individual brightway packages directly
import bw2analyzer as ba
import bw2calc as bc
import bw2data as bd
import bw2io as bi
#importing most important data science packages —› those are suggested by brightway getting started protocol —› so change it as you need in the future
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
#STARTING A PROJECT
#selecting a project for bw
bd.profect.set_current(name='<name_incomming>')

