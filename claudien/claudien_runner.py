import subprocess
import os
from time import sleep
import signal
from datetime import datetime
import threading
from claudien.claudien_to_prolog import convert
module_path = os.path.dirname(os.path.abspath(__file__))

def print2(*strings):
    print(datetime.now().strftime("%H:%M:%S"), " ".join(strings))

def train(game,timeout):
    for pred in os.listdir(module_path + "/input/{}".format(game)):
        #print2("game", game, "pred", pred)
        result = call_main(module_path + "/input/{}/{}".format(game,pred), timeout)
        #print("hello")
        yield result

    #send_finished_working()

def train_target(game,timeout,target):
    return call_main(module_path + "/input/{}/{}.pl".format(game,target), timeout)

def train_target_dataset(game,timeout,target, dataset_path):
    p = call_main(dataset_path, timeout)
    convert(game,target)
    return p

def get_nb_targets(game):
    return len(os.listdir(module_path + "/input/{}".format(game)))


def call_main(game,timeout):
    p = subprocess.Popen(["python2", module_path + "/system/learn.py", "claudien", game], stdin=subprocess.PIPE)
    counter = 0
    while p.poll() is None and counter < timeout:
        #print(game,':',counter)
        sleep(1)
        counter +=1

    result = (False,game.split("/")[-1].split(".")[0])
    if(counter >= timeout):
        p.send_signal(signal.SIGINT)
        sleep(10)
        result = (True,game.split("/")[-1].split(".")[0])
    p.terminate()
    return result

if __name__ == "__main__":
    for game in listdir("input"):
        train(game, 60)
