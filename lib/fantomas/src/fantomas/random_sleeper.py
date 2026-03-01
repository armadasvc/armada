import time
import random


def rsleep(sleeping_time, activate_random=True):
    if activate_random:
        sleeping_time = sleeping_time * random.uniform(0.8, 1.2)
    time.sleep(sleeping_time)