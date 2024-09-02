from pyH2A.Utilities.input_modification import insert, process_table, read_textfile
#SETTING UP BW
#importing individual brightway packages directly
import bw2analyzer as ba
import bw2calc as bc
import bw2data as bd
import bw2io as bi
from bw2io.importers.json_ld import JSONLDImporter
#importing most important data science packages —› those are suggested by brightway getting started protocol (https://learn.brightway.dev/en/latest/content/notebooks/BW25_for_beginners.html#section1)
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import os
import json
import pprint as pp
#
class Background_LCI_Database_Plugin_Option1:
    '''Processing of background data for brightway and running brightway.'''

    def __init__(self, dcf, print_info):

        process_table(dcf.inp, 'Foreground LCI Database', 'Value')
        self.running_brightway(dcf)

    def running_brightway(self, dcf):
        #WORK WITH A PROJECT
        #creating a new project
        name = "testing_240828" #when you change the name here then the project is directly added to the list of the projects
        bd.projects.set_current(name) #this activates the project and creates it if it's not existent
        #listing all available projects and checking if "name" was added to the project list
        #print(bd.projects)
        #
        #DATABASES
        bi.bw2setup()
        #print(bd.databases) 
        #pp.pprint(list(bd.methods)[:10])
        #
       # db = bd.Database(name)
       # foreground_database = dcf.inp['Foreground LCI Database']['Row']['Value']
       # db.write(foreground_database)
        fp = dcf.inp['Foreground LCI Database']['Row']['Value']
        importer = JSONLDImporter(fp)
        importer.apply_strategies()

    

        
        



