import os
import subprocess
import pathlib
import shutil
import sys

# Loop:
#   1. Simulator runs and outputs data to disk. It uses the last produced model as input, or nothing if it is the first run
#   2. Joiner takes this data, joins the observations and produces a cooked log. This file is persisted as <ITERATION>_joined.dsjson
#   3. VW is run using that cooked log as the input. It takes the last trained model as input and produces a model to be used on the next run. It is persisted as <ITERATION>.model


def run_command(command):
    result = subprocess.run(
        command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    if result.returncode != 0:
        print("\"{}\" failed with exit code:{}".format(
            " ".join(command), result.returncode))
        sys.exit(result.returncode)
    return result


def run_iteration(past_id, current_id, SIMULATOR_EXE, JOINER_EXE, VW_EXE, EXTRA_VW_ARGS):
    # Remove existing input models without id in name as they may be stale.
    if os.path.exists("input.model"):
        pathlib.Path("input.model").unlink()

    # If there is a past model, copy it into the name required for simulator.
    if past_id is not None:
        print("\tPast model found, using for simulator")
        dest = shutil.copyfile(past_id + ".model", "input.model")

    print("\tRunning simulator...")
    result = run_command([SIMULATOR_EXE])
    sim_output = result.stdout.decode("utf-8")
    print("\t\tLast line of output: " + sim_output.splitlines()[-1])

    print("\tRunning joiner...")
    result = run_command([JOINER_EXE, "-j", "true"])
    data_file_name = "{}_joined.dsjson".format(current_id)
    with open(data_file_name, 'w') as joined_log:
        joined_log.write(result.stdout.decode("utf-8"))

    print("\tRunning VW...")
    input_model = []
    if past_id is not None:
        input_model = ["-i", past_id + ".model"]
    output_model = ["-f", current_id + ".model"]
    args = [VW_EXE, "--dsjson", "-d", data_file_name, "--id", current_id]
    args.extend(EXTRA_VW_ARGS.split())
    args.extend(output_model)
    args.extend(input_model)
    print("\t\t" + " ".join(args))
    result = run_command(args)