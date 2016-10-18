#!/usr/bin/env python
##
##
## Given a path to original SEC cdf data directory,
##   Iterate through data directory looking for exp_singnalID.cdf
##   extract the ordinate_values within and generate a single JSON file
##   per signal channel for visualization purpose
##   extract meta data and store as a separate file_meta.json file
##   extract baseline information and store as a separate 
##                                             file_base.json file
##
## usage: ./processRAWCDF.py dataDir outDir
##
##     will produce outdir/dataSet1.json
##                  ...
##     will produce outdir/dataSetN.json
##
## The data directory should be setup with cdf file with complete name like
##    IMPT6749_NTX_E2-3_012216-SIGNAL01.cdf
##
##./processRAWCDF.py GPCR/EXP1 resultLoc
##./processRAWCDF.py GPCR/EXP1/GPCRUSC20161012EXP2_3_SIGNAL03.cdf resultLoc
##
## ** remember to install netCDF4, python package


import os
import sys
import pdb
import numpy as np

## blocking it before being called
import matplotlib 
matplotlib.use('Agg')

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
            'actual_sampling_interval',
            'actual_run_time_length', 'actual_delay_time' ]

attrlist=[ 'sample_name', 'detector_unit', 'detector_name',
           'injection_date_time_stamp', 'detection_method_name',
           'sample_id', 'dataset_completeness', 'aia_template_revision',
           'netcdf_revision','languages','HP_injection_time',
           'retention_unit', 'experiment_title', 'operator_name', 
           'separation_experiment_type' ]

dimlist=[ 'point_number', 'peak_number', 'error_number']

## list to dictionary
def list2dictionary(list):
    blist = {i: list[i] for i in range(0, len(list))}
    return blist

## every json needs to have a time series data
def process_for_data(target,dataloc) :
    if os.path.isfile(dataloc) :
      dir = ""
      onlyfiles = [dataloc]
    else :
      dir = dataloc
      onlyfiles = [f for f in os.listdir(dir) if os.path.isfile(os.path.join(dir, f))]
    
    for file in onlyfiles:
        if file.endswith('.cdf'):
            jlist={} 
            # remove cdf part and also the path info
            targetfile = file[:-4]
            head,tail=os.path.split(targetfile)

            tlist,vlist,mlist,slist=process_for_file(dir,file)
            key=tail
            time_key=key+"_time"
            meta_key=key+"_meta"

            fullpath=os.path.join(target,key)

            f = open(fullpath+".json", 'w')
            tmplist=list2dictionary(vlist)
            jlist[key]=tmplist
            jlist[time_key]=tlist
            f.write(json.dumps(jlist))
            f.close()
            alist={} 
            m = open(fullpath+"_meta.json", 'w')
            alist[meta_key]=mlist
            m.write(json.dumps(alist))
            m.close()
            s = open(fullpath+"_base.json", 'w')
            blist={}
            blist[key]=slist
            s.write(json.dumps(blist))
            s.close()
        else:
            continue
    exit(0)


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

def generate_base_list(mlist):
    print 'peak_number:', mlist['peak_number']
    print 'baseline_start_time:', mlist['baseline_start_time']
    print 'baseline_stop_time:', mlist['baseline_stop_time']
    p=mlist['peak_number']
    ilist={}
    for i in range(0, p) :
      item={}
      item['start_time']=mlist['baseline_start_time'][i]
      item['stop_time']=mlist['baseline_stop_time'][i]
      ilist[i]=item
    blist={}
    blist['text']='predefined baselines from hdf input file'
    blist['segment']=ilist
    blist['context']='default'
   
    zlist={ 'original': blist } 
    return zlist

def explode_dim(inputgrp, mlist):
    for dimobj in inputgrp.dimensions.values():
      if dimobj.name in dimlist:
        if DEBUG_PRINT:
          print "dim:", dimobj.name, ">>",dimobj.size 
        n = dimobj.name
        f = n.encode(encoding)
        mlist[f]=dimobj.size
   
def explode_value(inputgrp, mlist, f):
    t=inputgrp.variables[f].getValue().tolist()
    if DEBUG_PRINT:
      print "value:", f,">>", t
    mlist[f]=t

## f(peak_number)
def explode_peak(inputgrp, mlist, f):
    t=inputgrp.variables[f]
    if len(t) == 0 :
      mlist[f]= []
      if DEBUG_PRINT:
        print "peak:", f,">>", []
    else :
      t=t[:]
      m = [i.item() for i in t]
      if DEBUG_PRINT:
        print "peak:", f,">>", m
      mlist[f]= m

def explode_code(inputgrp, mlist, f):
    v=inputgrp.variables[f]
    if len(v) == 0:
      mlist[f]=[]
      if DEBUG_PRINT:
        print "code:", f,">>", []
    else:
      t=v[:].tolist()
      if DEBUG_PRINT:
        print "code:", f,">>", t
      mlist[f]=t

def explode_attribute(inputgrp, mlist, f):
    t=getattr(inputgrp,f)
    t=t.encode(encoding)
    if DEBUG_PRINT:
      print "attr:", f,">>",t
    mlist[f]=t


def process_for_file(dir,file):
    inputgrp = Dataset(os.path.join(dir,file), 'r')
    mlist={}
#    print "====="
#    print inputgrp.variables.keys
#    print "^^^^^"


## <type 'netCDF4._netCDF4.Variable'>
### extract variables

    explode_dim(inputgrp, mlist)

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
##<type 'netCDF4._netCDF4.Variable'>
    ordinate_values=inputgrp.variables['ordinate_values']
    cnt=len(ordinate_values)
## unicode
    retention_unit=getattr(inputgrp,'retention_unit')
    retention_unit=retention_unit.encode(encoding)
## generate an array of x points
    xlist=generate_x_array(retention_unit,actual_sampling_interval,cnt) 

## generate baselist 
    slist=generate_base_list(mlist)
    
## <type 'numpy.ndarray'>
    values=ordinate_values[:]
    vlist=values.tolist()

    max_v=max(vlist)
    min_v=min(vlist)
    print("max data",max_v)
    print("max idx",vlist.index(max_v))
    print("min data",min_v)
    print("min idx",vlist.index(min_v))

    inputgrp.close()

#    figure()
#    plot(values)
#    show()

    return xlist,vlist,mlist,slist
   

################ MAIN #################################

if(len(sys.argv) < 3) :
  print "Usage: processRawSEC.py [dataDir|datafile] outDir"
  exit(1)

dataloc=sys.argv[1]
outdir=sys.argv[2]

ff=os.path.islink(dataloc)
fff=os.path.isfile(dataloc)

if not os.path.exists(dataloc) and not os.path.isfile(dataloc):
  exit(1)

if not os.path.exists(outdir):
  os.mkdir(outdir)

process_for_data(outdir,dataloc)

