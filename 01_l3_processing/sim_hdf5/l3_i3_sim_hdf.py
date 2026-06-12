#!/bin/sh /cvmfs/icecube.opensciencegrid.org/py3-v4.3.0/icetray-start
#METAPROJECT: icetray/v1.9.2
from icecube import icetray, dataclasses, simclasses, dataio, tableio, toprec

from icecube.hdfwriter import I3HDFWriter
from icecube.icetray import I3Tray
from icecube.icetop_Level3_scripts.functions import count_stations

import sys 
import numpy as np
from argparse import ArgumentParser
from glob import glob


def add_IceTop_quality_cuts(frame):
    passed = all(frame['IT73AnalysisIceTopQualityCuts'].values())
    #print "test " + str(passed)
    frame['passed_IceTopQualityCuts'] = icetray.I3Bool(passed)


def add_nstations(frame, pulses='IceTopHLCSeedRTPulses_SnowUnAttenuated'):
    nstation = count_stations(dataclasses.I3RecoPulseSeriesMap.from_frame(frame, pulses))
    frame['NStations'] = icetray.I3Int(nstation)


parser = ArgumentParser(description=__doc__)
parser.add_argument('fname', type=str)
parser.add_argument('infile', nargs='+', type=str)
#parser.add_argument('outfile')
opts = parser.parse_args()


#physics = glob("/data/exp/IceCube/"+year+"/filtered/level2/*/Level2_IC86_corsika_icetop.010410.*.i3.bz2")
#physics = glob("/data/ana/CosmicRay/IceTop_level3/sim/IC86.2012/SIBYLL2.1/He/12630_v1s/Level3_IC86.2012_SIBYLL2.1_He_12630*.i3.*")

#change this line if you are changing which simulation you are using
#physics = glob("/data/ana/CosmicRay/IceTop_level3/sim/IC86."+year+"/SIBYLL2.3*/"+particle+"/"+str(fnum)+"_v1s/Level3_IC86."+year+"_SIBYLL2.3_"+particle+"_"+str(fnum)+"*.i3.*")

#Parse eitehr wildcard or list of files:
physics = []
for pattern in opts.infile:
    file_list = glob(pattern)
    physics.extend(file_list)

#physics = glob(opts.infile)

#physics = glob("/data/ana/CosmicRay/IceTop_level3/exp/IC86."+str(run_year)+"/"+str(year)+"/*/Level3_IC86."+str(run_year)+"*0_Subrun*.i3.*")

#/data/ana/CosmicRay/IceTop_level3/sim/IC86.2012/"+dataset+"/Level3_IC86.2012_"+dataset+"_Run0*.i3.gz")    # glob() the list of files from the disk

physics.sort()

#for i in physics:
#    print(i)
if len(physics)==0:
    print("This didn't work - no files globbed")

#gcd = '/data/ana/CosmicRay/IceTop_level3/sim/IC86.2012/GCD/Level3_'+dataset+'_GCD.i3.gz'
#gcd = '/home/mplum/GeoCalibDetectorStatus_2012.56063_V1_OctSnow_scint.i3'
subevent = 'IceTopSplit'


if len(physics)!=0:
    tray = I3Tray()
    #tray.AddModule('I3Reader', 'reader', filenamelist=opts.infile)
    tray.AddModule('I3Reader', 'reader', DropBuffers= False, filenamelist=physics)

    tray.Add(add_nstations,
             If=lambda frame: 'IceTopHLCSeedRTPulses_SnowUnAttenuated' in frame)

    tray.Add(add_IceTop_quality_cuts,
             If=lambda frame: 'IT73AnalysisIceTopQualityCuts' in frame)

    #you may need to update the keys if you change the simulation you are using
    tray.AddSegment(I3HDFWriter, 'scribe',
                    Output=opts.fname,
                    Keys=[
                        'I3TopInjectorInfo',
                        'I3EventHeader',
                        'QFilterMask',
                        'Laputop',
                        'LaputopParams',
                        'IT73AnalysisIceTopQualityCuts',
                        'NStations',
                        'MCPrimary',
                        'MCPrimaryInfo',
                        'ShowerPlane',
                        'ShowerPlaneParams'
                    ],
                    Types=[],
                    SubEventStreams=[subevent],
                    #DropOrphanStreams=[icetray.I3Frame.DAQ],
                    #streams=[icetray.I3Frame.Physics],
                   )

    tray.Execute()
