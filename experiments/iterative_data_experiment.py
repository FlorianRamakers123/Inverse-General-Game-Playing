import os
import sys
module_path = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(1, '../')
from base_experiment import run

systems = ["claudien"]
games = ["buttons_and_lights", "scissors_paper_stone"]
nb_experiments = 3
nb_divisions = 4

def run_experiment():
    datasets = []
    for i in range(nb_experiments):
        #i +=1
        # collect the datasets
        s = []
        for j in range(nb_divisions):
            s.append("cwa_dataset{}_{}".format(i+1,j+1))
        datasets.extend(s)
	# run experiment
    print(datasets)
    run(systems,games,datasets,"iterative_experiment")

if __name__ == "__main__":
    run_experiment()
