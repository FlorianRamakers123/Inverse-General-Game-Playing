import numpy
import matplotlib
import matplotlib.pyplot as plt
from collections import defaultdict


def calculate_mean_experiments(system, game):
    global DIVISIONS
    f = open("results/iterative_experiment/{}_{}_global_overview.csv".format(game,system))
    data = {}
    for line in f.readlines()[1:]:
        #line = line.replace('"', '')
        #print(line)
        data[line.split(",")[0][1:-1]] = (float(line.split(",")[1].strip()[1:-1]), float(line.split(",")[2].strip()[1:-1]), float(line.split(",")[3].strip()[1:-1]))
    f.close()

    print(data)
    """
  {'dataset3_2': ('.463', '.466', '.000'), 'dataset3_3': ('.463', '.466', '.000'),
  'dataset4_1': ('.656', '.660', '.000'), 'dataset4_2': ('.656', '.660', '.000'),
  'dataset4_3': ('.656', '.660', '.000'), 'dataset5_1': ('.656', '.660', '.000'),
  'dataset5_2': ('.656', '.660', '.000'), 'dataset5_3': ('.656', '.660', '.000')}

    """
    total = defaultdict(list)
    for datasetname in data.keys():
        d_nb = datasetname[-1:]
        total["dataset" + d_nb].append( data[datasetname] )

    experiments = set()
    for datasetname in data.keys():
        exp_nr = datasetname[7:8]
        experiments.add(exp_nr)
    nb_experiments = len(experiments)
    print("nb exp: ", nb_experiments)

    for k in total.keys():
        length = len(total[k])
        s = tuple(map(sum, zip(*total[k])))
        total[k] = tuple(map(lambda x: x/length, list(s)))


    #sort dict on key
    total_sorted = {}
    for key in sorted(total.keys()):
        total_sorted[key] = total[key]
    print(total_sorted)
    DIVISIONS = len(total.keys()) + 1
    return list(total_sorted.values())

DIVISIONS = None

def create_compare_graph_iterative_exp(game):
    f = open("results/base_experiment/{}_claudien_global_overview.csv".format(game))
    lines = f.readlines()
    f.close()
    max_data = tuple([s.strip()[1:-1] for s in lines[2].split(',')[1:]])
    data = calculate_mean_experiments("claudien", game) + [max_data]
    x_data = [1/DIVISIONS * (i+1) * 100 for i in range(DIVISIONS)]

    p_c = numpy.array([float(p) for (p,r,a) in data])
    r_c = numpy.array([float(r) for (p,r,a) in data])
    a_c = numpy.array([float(a) for (p,r,a) in data])
    x = numpy.array(x_data)

    f = open("results/base_experiment/{}_ilasp_global_overview.csv".format(game))
    lines = f.readlines()
    f.close()
    max_data = tuple([s.strip()[1:-1] for s in lines[2].split(',')[1:]])
    data = calculate_mean_experiments("ilasp", game) + [max_data]
    x_data = [1/DIVISIONS * (i+1) * 100 for i in range(DIVISIONS)]

    p_i = numpy.array([float(p) for (p,r,a) in data])
    r_i = numpy.array([float(r) for (p,r,a) in data])
    a_i = numpy.array([float(a) for (p,r,a) in data])

    # create AER graph
    plt.plot(x,a_c,label="kans op fout (Claudien)")
    plt.plot(x,a_i,label="kans op fout (ILASP)")
    plt.legend()
    plt.xlim(left=-1)
    plt.xlim(right=101)
    plt.ylim(bottom=-0.01)
    plt.xlabel("hoeveelheid data (in %)")
    plt.savefig('graphs/{}_aer.png'.format(game))
    plt.close()

    # create precision and recall graph
    plt.plot(x,p_c,label="precision (Claudien)")
    plt.plot(x,p_i,label="precision (ILASP)")
    plt.plot(x,r_c,label="recall (Claudien)")
    plt.plot(x,r_i,label="recall (ILASP)")
    plt.legend()
    plt.xlim(left=-1)
    plt.xlim(right=101)
    plt.ylim(bottom=-0.01)
    plt.xlabel("hoeveelheid data (in %)")
    plt.savefig('graphs/{}_p_r.png'.format(game))
    plt.close()

def create_global_graph_iterative_exp(system,game):
    f = open("results/base_experiment/{}_{}_global_overview.csv".format(game,system))
    lines = f.readlines()
    max_data = tuple([s.strip()[1:-1] for s in lines[1].split(',')[1:]])
    #f = open("results/iterative_experiment/{}_{}_global_overview.csv".format(game,system))

    data = calculate_mean_experiments(system, game) + [max_data]
    x_data = [1/DIVISIONS * (i+1) * 100 for i in range(DIVISIONS)]
    print(x_data)
    #f.close()
    print(data)

    p = numpy.array([float(p) for (p,r,a) in data])
    r = numpy.array([float(r) for (p,r,a) in data])
    a = numpy.array([float(a) for (p,r,a) in data])
    x = numpy.array(x_data)

    plt.plot(x,p,label="precision")
    plt.plot(x,r,label="recall")
    plt.plot(x,a,label="kans op fout")
    plt.legend()
    plt.xlim(left=-1)
    plt.xlim(right=101)
    plt.ylim(bottom=-0.01)
    #plt.ylim(top=1.1)
    #plt.title("Iteratief toevoegen van data")
    plt.xlabel("hoeveelheid data (in %)")
    plt.savefig('graphs/{}_{}_p_r_aer.png'.format(system,game))
    plt.close()


if __name__ == "__main__":
    import sys
    """
    if len(sys.argv) == 3:
        system = sys.argv[1]
        game = sys.argv[2]
        create_global_graph_iterative_exp(system,game)

    if len(sys.argv) == 2:
        print("plotting all games")
        system = sys.argv[1]
        for game in ["buttons_and_lights", "fizzbuzz", "scissors_paper_stone"]:
            create_global_graph_iterative_exp(system,game)

    if len(sys.argv) == 1:
        print("plotting for All systems, all games")
        for system in ["claudien", "ilasp"]:
            for game in ["buttons_and_lights", "fizzbuzz", "scissors_paper_stone"]:
                create_global_graph_iterative_exp(system,game)
    """
    create_compare_graph_iterative_exp(sys.argv[1])
