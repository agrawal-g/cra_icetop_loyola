import numpy as np
import glob
import os
import random
from pathlib import Path
from npx4.pysubmit import pysubmit
import subprocess
import argparse

# Creates jobs and DAG that process burnsample into hdf5 files, one per month of data
def create_bs_hdf(years, submit_dir, output_dir, sublines, job_name, cmd):
    header = ['#!/bin/bash ']
    for run_year in years[:-1]:
        for year in [run_year]:
            for month in range(4, 13):
                #files = sorted(glob.glob('/data/ana/CosmicRay/IceTop_level3/exp/IC86.{run_year}_pass2_v0*/{year}/*/Run*0/Level3_IC86.{run_year}*0_Subrun*.i3.*'.format(run_year = run_year, year = year)))
                #if len(files) > 0:
                jobID = '{job_name}_{no}_{id}'.format(job_name = job_name, no = str(year)+str(month).zfill(2), id = random.randint(0,99999))
                ex = [cmd, output_dir, str(run_year), str(year), str(month).zfill(2)]
                    #ex.extend(files)
                ex = ' '.join(ex)
                pysubmit(ex, sublines=sublines, jobID=jobID, outdir=submit_dir, header=header,
                         condor_dag = '{sub}/{job_name}.dag'.format(sub = submit_dir, job_name=job_name))
        for year in [run_year+1]:
            for month in range(1, 8):
                #files = sorted(glob.glob('/data/ana/CosmicRay/IceTop_level3/exp/IC86.{run_year}_pass2_v0*/{year}/*/Run*0/Level3_IC86.{run_year}*0_Subrun*.i3.*'.format(run_year = run_year, year = year)))
                #if len(files) > 0:
                jobID = '{job_name}_{no}_{id}'.format(job_name = job_name, no = str(year)+str(month).zfill(2), id = random.randint(0,99999))
                ex = [cmd, output_dir, str(run_year), str(year), str(month).zfill(2)]
                #    ex.extend(files)
                ex = ' '.join(ex)
                pysubmit(ex, sublines=sublines, jobID=jobID, outdir=submit_dir, header=header,
                         condor_dag = '{sub}/{job_name}.dag'.format(sub = submit_dir, job_name = job_name))
    try:
        result = subprocess.run(["condor_submit_dag", '{sub}/{job_name}.dag'.format(sub = submit_dir, job_name = job_name)], capture_output=True, text=True)
        print("DAG submission output:", result.stdout)
        if result.returncode == 0:
            print("DAG file submitted successfully.")
        else:
            print("Error submitting DAG file:", result.stderr)
    except Exception as e:
        print("Failed to submit DAG file: {ex}".format(ex = e))

# Creates jobs and DAG that processes data (burnsample or all) into root
def create_submit_files(years, submit_dir, output_dir, sublines, job_name, cmd, all_data):
    # Environment for script
    header = ['#!/bin/bash ']
    for year in years:
        year_submit_dir = '{sub}/{yr}'.format(sub = submit_dir, yr = year)
        if not os.path.isdir(year_submit_dir):
            os.makedirs(year_submit_dir)
        for month in range(1, 13):
            for day in range(1,32):
                date = str(month).zfill(2)+str(day).zfill(2)
                if all_data:
                    files = sorted(glob.glob('/data/ana/CosmicRay/IceTop_level3/exp/IC86.*_pass2_v0*/{year}/{date}/Run*/Level3_IC86.*Subrun*.i3.*'.format(year = year, date=date)))
                    files = [f for f in files if 'IC86.2018_pass2_v02' not in f]
                else:
                    files = sorted(glob.glob('/data/ana/CosmicRay/IceTop_level3/exp/IC86.*_pass2_v0*/{year}/{date}/Run*0/Level3_IC86.*0_Subrun*.i3.*'.format(year = year, date=date)))
                if len(files) > 0:
                    jobID = '{name}_{no}_{id}'.format(name = job_name, no = str(year)+date, id = random.randint(0,99999))
                    #add run year?
                    ex = [cmd, output_dir, str(year), date]
                    ex.extend(files)
                    ex = ' '.join(ex)
                    pysubmit(ex, sublines=sublines, jobID=jobID, outdir=year_submit_dir, header=header,
                             condor_dag = '{sub}/{name}_{yr}.dag'.format(name = job_name, sub = year_submit_dir, yr = year))
        try:
            result = subprocess.run(["condor_submit_dag", '{sub}/{name}_{yr}.dag'.format(name = job_name, sub = year_submit_dir, yr = year)], capture_output=True, text=True)
            print("DAG submission output:", result.stdout)
            if result.returncode == 0:
                print("DAG file submitted successfully.")
            else:
                print("Error submitting DAG file:", result.stderr)
        except Exception as e:
            print("Failed to submit DAG file: {ex}".format(ex = e))

# Main method
if __name__ == "__main__":
    # Set up command line options
    parser = argparse.ArgumentParser(description=
                                     "Process data l3.i3 files as either hdf5 or root files.")
    parser.add_argument("--hdf", dest="hdf", type=str, default=None,
                        help="Output directory for hdf5 files")
    parser.add_argument("--root", dest="root", type=str,
                        default=None, help="Output directory for root files")
    parser.add_argument("-y", "--years", dest="years", nargs="*", type=int,
                        default= [2011, 2012, 2013, 2014, 2015, 2016, 2017, 2018, 2019, 2020, 2021, 2022],
                        help="Calendar years to run (default all 2011-22).")
    #parser.add_argument("-m", "--memory", dest="memory", type=int, default=4000, help="Amount of MB to request (int).")
    parser.add_argument("--all_data", dest="all_data", action='store_true', default=False, help="Run for all data instead of burnsample")
    args = parser.parse_args()

    #Get absolute path of directory 
    abs_path = Path(__file__).resolve().parent

    #Burnsample -> HDF5
    if args.hdf != None:
        #Set directories and commands
        #Submit
        submit_dir = './submit_hdf'
        if not os.path.isdir(submit_dir):
            os.makedirs(submit_dir)

        #Output
        output_dir = args.hdf
        if not os.path.isdir(output_dir):
            os.makedirs(output_dir)

        #JobID and cmd
        job_name = "hdfprod"
        script_name = '{path}/l3_i3_burnsample_hdf.py'.format(path = abs_path)
        #Memory?
        sublines = ['request_memory = 2000', 'request_disk = 2 MB']

        create_bs_hdf(args.years, submit_dir, output_dir, sublines, job_name, script_name)

    # DATA (Burnsample OR All) -> ROOT
    if args.root != None:
        #Set directories and commands
        #Submit
        submit_dir = './submit_root'
        if not os.path.isdir(submit_dir):
            os.makedirs(submit_dir)

        #Output
        output_dir = args.root
        if not os.path.isdir(output_dir):
            os.makedirs(output_dir)

        #JobID and cmd
        script_name = '{path}/l3_i3_to_root_day.py'.format(path = abs_path)
        if args.all_data:
            job_name = "rootprod"
        else:
            job_name = "rootburn"
        #Memory?
        sublines = ['request_memory = 6000', 'request_disk = 2 MB']
            
        create_submit_files(args.years, submit_dir, output_dir, sublines, job_name, script_name, args.all_data)
