import os

import environ

env = environ.Env(DEBUG=(bool, False))

# Retrieving the paths
current_path = environ.Path(__file__) - 1
project_root = current_path - 2
env_file = project_root(".env")

if os.path.exists(env_file):
    environ.Env.read_env(env_file)
