import argparse
import re

from gen_base import * 
from gen_sched import * 
from gen_task import * 
from gen_arrival import *

import sys
import os

def print_list(out, f, ll, sep = ",") :
    """ 
    Calls function f on every element of ll. 
    The results should be a string which is printed on out. 
    All strings are separated by sep. 
    """
    fl = False
    first = True
    for x in ll :
        s = f(x);
        if s != "" : 
            if not first :
                out.write(sep + " ")
            out.write(s)
            first = False    
            fl = True
    return fl
    
def prop_extract(x, n, t) :
    """
    Expects a property string x formatted as " nn = vv ", where nn is
    a string, and v is a value (a string).  If the string nn matches
    the input parameter n, then the pair <n, v> is stored into
    dictionary t. Automatically strips all spaces
    """
    x = x.strip()
    if x.startswith(n) :
        t[n] = x.split('=')[1].strip()
        return True
    else :
        return False

def list_extract(x, n, t) :
    """
    like prop_extract, but it expects a list after the '='
    the list is in the form [a ; b; ...]
    """
    x = x.strip()
    if x.startswith(n) :
        temp = x.split('=')[1].strip()
        temp = stripsq(temp)
        l = temp.split(';')
        l = [y.strip() for y in l]
        t[n] = l
        return True
    else :
        return False


def parse_periodic(l) :
    per = {}
    l = l.strip()
    s = l.split(',')
    for x in s :
        prop_extract(x, 'name', per)
        prop_extract(x, 'period', per)
    return per


def parse_merge(l) :
    mer = {}
    l = l.strip()
    s = l.split(',')
    for x in s :
        prop_extract(x, 'name', mer)
        prop_extract(x, 'tname', mer)
        list_extract(x, 'list', mer)
    return mer

def parse_ptask(l) :
    """ 
    Expects a line string starting with ptask, and containing a set of
    properties separated by commas. The possible properties are: name,
    ctime, period, deadline.  Currently, it does not check that all
    properties are in order, nor that they are all present.
    """
    task = {}
    l = l.strip()
    s = l.split(',')
    task['max_inst'] = 3
    for x in s :
        prop_extract(x, 'name', task)
        prop_extract(x, 'ctime', task)
        prop_extract(x, 'period', task)
        prop_extract(x, 'deadline', task)        
        prop_extract(x, 'max_inst', task)
    return task


def parse_curve(l) :
    cur = {}
    s = l.strip().split(',')
    print s
    for x in s :
        prop_extract(x, 'name', cur)
        prop_extract(x, 'tname', cur)
        prop_extract(x, 'period', cur)
        prop_extract(x, 'burst', cur)
    return cur


    
def parse_input(inputfile) :
    """
    Parses an input file containing specification for periodic tasks, 
    or for schedulers, and creates the corresponding automata. 
    Returns a list of automata objects. 
    """
    inp = open(inputfile, 'r')
    lines = inp.readlines()
    inp.close()

    ll = []
    tnames = []
    for l in lines :
        if l.startswith("--"):
            continue
        elif l.startswith('task') :
            l = l.lstrip('task')
            task = parse_ptask(l)
            ll.append(task_automaton(task['name'], task['ctime'], task['deadline'], task['max_inst']))
            tnames.append(task['name'])
        elif l.startswith('pdtask') :
            l = l.lstrip('pdtask')
            task = parse_ptask(l)
            ll.append(task_automaton(task['name'], task['ctime'], task['deadline'], task['max_inst']))
            ll.append(periodic_automaton(task['name']+"_arr", task['name'], task['period']))
            tnames.append(task['name'])
        elif l.startswith('ptask') :
            l = l.lstrip('ptask')
            task = parse_ptask(l)
            ll.append(task_impldline_automaton(task['name'], task['ctime'], task['name']+"_arr"))
            ll.append(periodic_automaton(task['name']+"_arr", task['name'], task['period']))
            tnames.append(task['name'])
        elif l.startswith('stask') :
            l = l.lstrip('stask')
            task = parse_ptask(l)
            ll.append(task_impldline_automaton(task['name'], task['ctime'], task['name']+"_arr"))
            ll.append(sporadic_automaton(task['name']+"_arr", task['name'], task['period']))
            tnames.append(task['name'])
        elif l.startswith("sched") :
            l = l.lstrip("sched")
            s = [x.strip() for x in l.split(',')]
            ll.append(sched_automaton(s[0], s[1:], False))
        elif l.startswith("idlesched") :
            l = l.lstrip("idlesched")
            s = [x.strip() for x in l.split(',')]
            ll.append(sched_automaton(s[0], s[1:], True))
        elif l.startswith('periodic') :
            l = l.lstrip('periodc')
            per = parse_periodic(l)
            ll.append(periodic_automaton(per['name']+"_arr", per['name'], per['period']))
        elif l.startswith('sporadic') :
            l = l.lstrip('sporadic')
            per = parse_periodic(l)
            ll.append(sporadic_automaton(per['name']+"_arr", per['name'], per['period']))
        elif l.startswith('merge') :
            l = l.lstrip('merge')
            mer = parse_merge(l)
            ll.append(merge_automaton(mer['name'], mer['list'], mer['tname']))
        elif l.startswith('curve') :
            l = l.lstrip('curve') 
            cur = parse_curve(l)
            ll.append(arrival_curve_automaton(cur['name'], cur['tname'], cur['burst'], cur['period']))
        else :
            print "ERROR in parsing the input file"
            exit
    ll.append(miss_automaton("dline", tnames))
    return ll


def search_dmiss(statesfile) :
    """
    Greps the states file for a deadline miss state. 
    """
    dmiss = False
    f = open(statesfile, 'r')
    ln = 0
    for line in f.readlines():
        ln = ln + 1
        if re.search("dline_loc_miss", line):
            dmiss = True
    return dmiss


def generate_imi(out, ll) :
    """
    Given a list of automatons, generates the imi file, 
    including the final deadline miss property. 
    """
    out.write("var\n")
    out.write("    ")
    if print_list(out, lambda x : x.gen_clocks(), ll) : out.write(" : clock;\n    ")
    if print_list(out, lambda x : x.gen_discrete(), ll) : out.write(" : discrete;\n    ")
    if print_list(out, lambda x : x.gen_parameters(), ll) : out.write(" : parameter;\n    ")
    out.write("\n\n")

    for x in ll :
        out.write(x.gen_automaton())
        out.write("\n\n")

    out.write("var init: region;\n\n")
    out.write("init := ")

    for x in ll :
        out.write(x.gen_init())
        out.write(x.gen_init_param())
    out.write("    True;\n")
    out.write("property := unreachable loc[OBS_dline] = dline_loc_miss\n")
    out.close()
    
def main() :
    parser = argparse.ArgumentParser(
        description='Generate a imi file for analysing a real-time system')
    
    parser.add_argument('file')
    parser.add_argument('--norun', action='store_true')
    parser.add_argument('--cover', action='store_true')
    parser.add_argument('--inverse', action='store_true')
    parser.add_argument('--depth', default = -1)
    parser.add_argument('--cart', action='store_true')
    parser.add_argument('--step', default = -1)

    args = parser.parse_args()

    print "Options: ", args

    inputfile = args.file
    imifile = args.file 
    v0file = args.file
    statesfile = args.file

    if not inputfile.endswith(".txt") :
        imifile = imifile + ".imi"
        v0file = v0file + ".v0"
        statesfile = statesfile + ".states"
    else :
        imifile = inputfile[0:-4] + ".imi"
        v0file = v0file[0:-4] + ".v0"
        statesfile = statesfile[0:-4] + ".states"
        
    print "Output files:", imifile, v0file

    out = open(imifile, 'w')

    ll = parse_input(inputfile)
    
    generate_imi(out, ll)

    # Generate the v0 file
    v0 = open(v0file, 'w')
    print_list(v0, lambda x: x.gen_parvalues(), ll, '&')

    v0.close()

    # if necessary, runs imitator
    if not args.norun :
        if args.cover :
            cmd = "../IMITATOR32 {0} {1} -mode cover -incl -merge -with-log".format(imifile,v0file)
            if args.cart : 
                cmd = cmd + " -cart"
                if args.step > -1 :
                    cmd = cmd + " -step {0}".format(args.step)
        elif args.inverse :
            cmd = "../IMITATOR32 {0} {1} -mode inversemethod -incl -merge -with-log".format(imifile,v0file)
        else :
            cmd = "../IMITATOR32 {0} -mode reachability -incl -merge -with-log".format(imifile)

        if args.depth > -1 :
            cmd = cmd + " -depth-limit {0}".format(args.depth)

        print "Running command: ", cmd
        os.system(cmd)

        if not args.cover :
            dmiss = search_dmiss(statesfile)                    
            if not dmiss : 
                print "No Deadline misses"   
            else :
                print "DEADLINE MISS FOUND!!"







if __name__ == "__main__" :
    main()
    

