import argparse
import sys
import os
import json
import subprocess
import re
from rich import print
import tempfile



def run_with_spack_load(spack_pkg, cmd, timeout=20):
    try:
        load_cmd = subprocess.check_output(["spack", "load", "--sh", spack_pkg])
    except subprocess.CalledProcessError:
        return None, 1

    output = None
    ret = 1

    with tempfile.NamedTemporaryFile(mode="w",suffix=".sh", delete=False) as f:
        f.write(load_cmd.decode(encoding="utf-8"))
        f.write("\n" + " ".join( ["\"{}\"".format(x) for x in cmd]))
        f.flush()
        f.close()
        try:
            output = subprocess.check_output(["sh", f.name], timeout=timeout)
            ret = 0
        except subprocess.TimeoutExpired:
            print("[bold red]Error: command timed out[/bold red]")
            ret = -1
        except subprocess.CalledProcessError as e:
            ret = e.returncode
        os.unlink(f.name)

    if output:
        output = output.decode(encoding="utf-8")

    return output, ret



def run_silent(cmd):
    with open("/dev/null", "w") as null:
        return subprocess.call(cmd, stdout=null, stderr=null)

class Implementation():

    def _check_exist(self):
        print("Checking for {} in spack ... ".format(self.name), end="")
        sys.stdout.flush()
        if run_silent(["spack", "spec", self.name]):
            print("[red]error[/red]")
            raise Exception("No such spack package '{}'".format(self.name))
        print("[green]OK[/green]")


    def _list_versions(self):
        version_text_list = subprocess.check_output(["spack", "info", self.name])
        expr = re.compile(r"\s+([0-9\.]+)\s+http.*",re.MULTILINE)
        versions = re.findall(expr, version_text_list.decode(encoding="utf-8"))
        if not versions:
            raise Exception("Cannot find any version for {}".format(self.name))
        return sorted(list(set(versions)))

    def _deploy_all(self):
        versions = self._list_versions()
        for v in versions:
            target = "{}@{}".format(self.name, v)
            if run_silent(["spack", "find", target]):
                if self.install:
                    print("[bold red]Now building {}[/bold red]".format(target))
                    if subprocess.call(["spack", "install", target]):
                        print("Failed to compile {}, ignoring".format(target))
                    else:
                        self.running_versions.append(v)
                else:
                    print("{} [yellow]Skipped[\yellow]".format(target))
            else:
                print("{} [green]Found[\green]".format(target))
                self.running_versions.append(v)


    def compile_and_run(self, file, timeout=20):
        multi_ret = []
        for v in self.running_versions:
            target = "{}@{}".format(self.name, v)
            print("!! Running {} against {}".format(file, target))
            with tempfile.NamedTemporaryFile(suffix=".exe", delete=False) as tempexe:
                tempexe.close()
                out, ret = run_with_spack_load(target, ["mpicc", file, "-o", tempexe.name], timeout)
                print("[bold blue]Compilation:[/bold blue]")
                print(out)
                if ret:
                    multi_ret.append({"version" : v,  "out" : None, "ret" : ret})
                    continue
                out, ret = run_with_spack_load(target,[tempexe.name], timeout)
                os.unlink(tempexe.name)
                print("[bold blue]Execution:[/bold blue]")
                print(out)
                multi_ret.append({"version" : v, "out" : out, "ret" : ret})
        return multi_ret




    def __init__(self, name, install=False):
        self.name = name
        self.install = install
        self.running_versions = []
        self._check_exist()
        self._deploy_all()


class Output():

    def __init__(self, f, runs, out=sys.stdout):
        self.format = f
        self.out = out
        self.runs = runs
        self._unfold()

    def _unfold(self):
        for m in self.runs.keys():
            # Clean nones
            self.runs[m] = [ x for x in self.runs[m] if x["out"]]
            for entry in self.runs[m]:
                if isinstance(entry["out"], dict):
                    continue
                try:
                    data = json.loads(entry["out"])
                    entry["out"] = data
                except json.JSONDecodeError:
                    pass

    def _md_unfold_to_list(self, values):
        filt = { k:v for (k,v) in values.items() if k != "_"}
        return "\n".join([ "* {} = {}".format(k,filt[k]) for k in filt.keys() ]) 

    def _md(self):
        ret = ""
        for m in self.runs.keys():
            ret = ret + "# {}\n\n".format(m)
            for entry in self.runs[m]:
                ret = ret + "## {}\n\n".format(entry["version"])
                if isinstance(entry["out"], str):
                    ret = ret + "```\n{}\n```\n".format(entry["out"])
                else:
                    ret = ret + self._md_unfold_to_list(entry["out"]) + "\n\n"
        return ret


    def render(self):

        if self.format == "json":
            self.out.write(json.dumps(self.runs))
        elif self.format == "md":
            self.out.write(self._md())
        else:
            pass



def cli_entry():

    parser = argparse.ArgumentParser(description='mpiscan MPI code inspector')

    parser.add_argument('-f', '--format', choices=['md', 'json'], default="json", help="Format to be used for outputing results (default is json)")
    parser.add_argument('-m', '--mpis', type=str, default="openmpi,mpich,intel-mpi,mvapich2",
                        help="Comma separated list of mpi spack recipes to use")
    parser.add_argument('-b', "--build",  action='store_true', help="Allow building attempt of missing MPI versions")
    parser.add_argument('-o', "--out", type=str, help="Store results in this file")

    parser.add_argument('-j', "--json", type=str, help="Previous JSON result file (source is not required as code is not run)")
    parser.add_argument('-s', "--source", type=str, help="File to be compiled and run for outputing results")



    args = parser.parse_args(sys.argv[1:])

    rets = {}

    if args.json:
        if not os.path.isfile(args.json):
            raise Exception("{} is not a regular file".format(args.json))

        with open(args.json, "r") as f:
            rets = json.load(f)
    else:
        source = args.source

        if not source:
            raise Exception("You need to provide a file to compile and run with -s/--source")

        if not os.path.isfile(source):
            raise Exception("{} is not a regular file".format(source))

        mpi_impls = []

        for i in args.mpis.split(","):
            mpi_impls.append(Implementation(i, install=args.build))

        for i in mpi_impls:
            rets[i.name] = i.compile_and_run(source)

    if args.out:
        fout = open(args.out, "w")
    else:
        fout = sys.stdout

    out = Output(args.format, rets, fout)
    out.render()

    if args.out:
        fout.close()
