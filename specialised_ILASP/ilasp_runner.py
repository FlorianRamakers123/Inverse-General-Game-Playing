import os
import sys
module_path = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(1, '../')
from utils.tokenlib import fix_not_ilasp, sort_ilasp_body

import subprocess
import re
import glob
import json

# inpudata is a path of a file in .dat format !!!!!!!!!!!!!!
def run_ilasp(outfile, game, subtarget, inputdata, time_out):
    f = open(module_path + outfile + "_rawoutput", 'w')
    cmd= module_path + "/GGP_ILASP {} {} {}/../types/{}.typ".format(subtarget, module_path + inputdata, module_path, game)
    #print(cmd)
    try:
        #timeout=1800
        subprocess.run(cmd.split(' '),timeout=time_out,stdout=f)
    except subprocess.TimeoutExpired:
        pass

    os.remove("out_{}".format(subtarget))
    os.remove("task_{}".format(subtarget))

    raw_output = open(module_path + outfile + "_rawoutput").read()
    final_hypothesis = ""
    for hyp in raw_output.split("{"):
        if "UNSATISFIABLE" not in hyp:
            final_hypothesis = hyp.split("}")[0]


    final_hypothesis = fix_not_ilasp(final_hypothesis.replace("succ(","succ1("))
    hyp = ""
    for line in final_hypothesis.split(".\n"):
        if line.strip() == "":
            continue
        parts = line.split(":-")
        if len(parts) > 1:
            parts[1] = sort_ilasp_body(parts[1])
            hyp += parts[0] + ":- " + parts[1] + ".\n"
        else:
            hyp += parts[0] + ".\n"

    print(hyp)
    with open(module_path + outfile, 'w') as ff:
        ff.write(hyp)

'''
len_args = len(sys.argv)
if len_args ==5: #4 argumenten opgegeven
    outfile = sys.argv[1]
    game = sys.argv[2]
    subtarget = sys.argv[3]
    inputdatafile = sys.argv[4]
    run(outfile, game, subtarget, inputdatafile)
else:
    print("outfile, game, subtarget, inputdata")
 '''
