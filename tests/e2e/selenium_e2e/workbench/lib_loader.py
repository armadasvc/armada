import sys

def local_lib_loader(path):
    absolute_paths_list = [path]
    for path in absolute_paths_list:
        if path not in sys.path:
            sys.path.append(path)
