#!/usr/bin/env python
##
##
## Given a path to original SEC data directory,
##   Iterate through all the subdirectory looking for dataSet.aia directory.
##   Iterate through all the subdirectory of datSet.aia for signalId.cdf
##   extract the ordinate_values within and generate a single JSON file
##   per signal channel for visualization purpose
##   extract meta data and store as a separate file_meta.json file
##
## usage: ./processRawSEC.py dataDir outDir
##
##     will produce outdir/dataSet1.json
##                  ...
##     will produce outdir/dataSetN.json
##
## The aia directory could be setup with a complete name like
##    MING/NTX_E2-3_012216.aia/IMPT6749_NTX_E2-3_012216-SIGNAL01.cdf
## or it could be 
##    KOR_construct_screening/IMPT4825_NTX_E2-3_020216.aia/SIGNAL01.cdf
##
##
## ** remember to install netCDF4, python package


import os
import sys
import pdb
import numpy as np
from netCDF4 import Dataset
from pylab import *
import json

encoding = 'utf8'
DEBUG_PRINT = 0

peaklist=[ 'peak_retention_time', 'peak_start_time', 'peak_end_time',
           'peak_width', 'peak_area', 'peak_area_percent', 'peak_height',
           'peak_height_percent', 'peak_asymmetry',  
           'baseline_start_time', 'baseline_start_value', 
           'baseline_stop_time', 'baseline_stop_value',
           'migration_time', 'peak_area_square_root',
           'manually_reintegrated_peaks' ]
codelist=[ 'peak_start_detection_code', 'peak_stop_detection_code' ]

valuelist=[ 'detector_maximum_value', 'detector_minimum_value',
            'actual_run_time_length', 'actual_delay_time' ]

attrlist=[ 'sample_name', 'detector_unit', 'detector_name',
           'injection_date_time_stamp', 'detection_method_name',
           'sample_id', 'dataset_completeness', 'aia_template_revision',
           'netcdf_revision','languages','HP_injection_time',
           'experiment_title', 'operator_name', 'separation_experiment_type' ]

## list to dictionary
def list2dictionary(list):
    blist = {i: list[i] for i in range(0, len(list))}
    return blist

## every json needs to have a time series data
def process_for_directory(target,dir) :
    onlyfiles = [f for f in os.listdir(dir) if os.path.isfile(os.path.join(dir, f))]
    for file in onlyfiles:
        if file.endswith('.cdf'):
            jlist={} 
            targetfile = file[:-4]
            tlist,vlist,mlist=process_for_file(dir,file)

            key= generate_dataset_name(target,targetfile)
            time_key=key+"_time"
            meta_key=key+"_meta"
            head,tail=os.path.split(target)
            fullpath=os.path.join(head,key)
            f = open(fullpath+".json", 'w')
            slist=list2dictionary(vlist)
            jlist[key]=slist
            jlist[time_key]=tlist
            f.write(json.dumps(jlist))
            f.close()
            alist={} 
            m = open(fullpath+"_meta.json", 'w')
            alist[meta_key]=mlist
            m.write(json.dumps(alist))
            m.close()
        else:
            continue

## generate a range of 'cnt' items in minutes
def generate_x_array(type,interval,cnt): 
    if type.find("seconds") != -1 :
      step=(interval/60)
    else:
      step=interval
    lastOne=round(step*(cnt-1))
    xRange=np.arange(0, lastOne, step)
    xlist=xRange.tolist()
    xxlist=list2dictionary(xlist)
    return xxlist

def generate_dataset_name(dir,fname):
    if fname.find("SIGNAL") == 0 :
      stub=os.path.basename(dir)
      return stub+"-"+fname
    else:
      return fname

def explode_value(inputgrp, mlist, f):
    t=inputgrp.variables[f].getValue().tolist()
    if DEBUG_PRINT:
      print "value:", f,t
    mlist[f]=t

## f(peak_number)
def explode_peak(inputgrp, mlist, f):
    t=inputgrp.variables[f]
    if len(t) == 0 :
      mlist[f]= []
      if DEBUG_PRINT:
        print "peak:", f,[]
    else :
      t=t[:]
      m = [i.item() for i in t]
      if DEBUG_PRINT:
        print "peak:", f,m
      mlist[f]= m

def explode_code(inputgrp, mlist, f):
    v=inputgrp.variables[f]
    if len(v) == 0:
      mlist[f]=[]
      if DEBUG_PRINT:
        print "code:", f,[]
    else:
      t=v[:].tolist()
      if DEBUG_PRINT:
        print "code:", f,t
      mlist[f]=t

def explode_attribute(inputgrp, mlist, f):
    t=getattr(inputgrp,f)
    t=t.encode(encoding)
    if DEBUG_PRINT:
      print "attr:", f,t
    mlist[f]=t


def process_for_file(dir,file):
    inputgrp = Dataset(os.path.join(dir,file), 'r')
    mlist={}
#    print "====="
#    print inputgrp.variables.keys
#    print "^^^^^"

## <type 'netCDF4._netCDF4.Variable'>
### extract variables

    for f in valuelist :
       explode_value(inputgrp, mlist, f)

    for f in peaklist :
       explode_peak(inputgrp, mlist, f)

    for f in codelist:
       explode_code(inputgrp, mlist, f)

    for f in attrlist:
       explode_attribute(inputgrp, mlist, f)

##numpy.ndarray
    actual_sampling_interval=inputgrp.variables['actual_sampling_interval'].getValue()
    actual_sampling_interval=actual_sampling_interval.tolist()
##float
    if DEBUG_PRINT:
      print "actual_sampling_interval ",actual_sampling_interval
    mlist['actual_sampling_interval']=actual_sampling_interval

##<type 'netCDF4._netCDF4.Variable'>
    ordinate_values=inputgrp.variables['ordinate_values']
    cnt=len(ordinate_values)
    if DEBUG_PRINT:
      print "ordinate_values length ",cnt
    mlist['ordinate_values_cnt']=cnt

## unicode
    retention_unit=getattr(inputgrp,'retention_unit')
    retention_unit=retention_unit.encode(encoding)
    if DEBUG_PRINT:
      print "retention_unit ",retention_unit
    mlist['retention_unit']=retention_unit

## generate an array of x points
    xlist=generate_x_array(retention_unit,actual_sampling_interval,cnt) 
    
## <type 'numpy.ndarray'>
    values=ordinate_values[:]
    vlist=values.tolist()

    inputgrp.close()

#    figure()
#    plot(values)
#    show()

    return xlist,vlist,mlist
   

################ MAIN #################################
if(len(sys.argv) < 3) :
  print "Usage: processRawSEC.py dataDir outDir"
  exit()

datadir=sys.argv[1]
outdir=sys.argv[2]

if not os.path.exists(datadir):
  exit()

if not os.path.exists(outdir):
  os.mkdir(outdir)

onlydirs = [d for d in os.listdir(datadir) if os.path.isdir(os.path.join(datadir, d))]

for dir in onlydirs:
    if dir.endswith('.aia'):
        targetdir = dir[:-4]
        target=os.path.join(outdir,targetdir)
        process_for_directory(target,os.path.join(datadir,dir))
    else:
        continue

