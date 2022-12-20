# MPI Scan

Run a code on multiple MPI implementations thanks to [spack](https://spack.io) and capture outputs.

## Install

```
git clone https://github.com/besnardjb/mpiscan.git
cd mpiscan
pip install .
```

## Run

```
usage: mpiscan [-h] [-f {md,json}] [-m MPIS] [-b] [-o OUT] [-j JSON] [-s SOURCE]

mpiscan MPI code inspector

optional arguments:
  -h, --help            show this help message and exit
  -f {md,json}, --format {md,json}
                        Format to be used for outputing results (default is json)
  -m MPIS, --mpis MPIS  Comma separated list of mpi spack recipes to use
  -b, --build           Allow building attempt of missing MPI versions
  -o OUT, --out OUT     Store results in this file
  -j JSON, --json JSON  Previous JSON result file (source is not required as code is not run)
  -s SOURCE, --source SOURCE
                        File to be compiled and run for outputing results
```

Compiling all MPI implementations with the `-b` (at least those working on your machine) can take time, if you want only to pick a few of them, install them manually with spack.


## Example Check MPI_BOTTOM and MPI_IN_PLACE

### Prepare Test File

We make a code which outputs a valid JSON dict, you may use a key `_` as dummy element (trailing commas).

```lang=c
#include <mpi.h>
#include <stdio.h>


#define PRINT_VALUE_SIZE( CONSTANT ) do{ \
unsigned int size = sizeof(CONSTANT);\
char value[64];\
snprintf(value, 64, "%ld", (long int)CONSTANT);\
printf("\"value_%s\" : %s,\n", #CONSTANT, value);\
printf("\"size_%s\" : %d,\n", #CONSTANT, size); }while(0)

int main(int argc, char** argv)
{
	MPI_Init(&argc, &argv);

   printf("{\n");


   PRINT_VALUE_SIZE(MPI_BOTTOM);
   PRINT_VALUE_SIZE(MPI_IN_PLACE);

   printf("\"_\" : null}\n");

	MPI_Finalize();
	return 0;
}

```

Sample output:

```lang=js
{
      '_': None,
      'size_MPI_BOTTOM': 8,
      'size_MPI_IN_PLACE': 8,
      'value_MPI_BOTTOM': 0,
      'value_MPI_IN_PLACE': 1,
}
```


### Run

```
mpiscan -b ./test.c -f md -o out.md
```

Consider using `-f json` for post-processing.


### Result


```lang=md
# openmpi

## 1.10.0

* value_MPI_BOTTOM = 0
* size_MPI_BOTTOM = 8
* value_MPI_IN_PLACE = 1
* size_MPI_IN_PLACE = 8

## 1.10.1

* value_MPI_BOTTOM = 0
* size_MPI_BOTTOM = 8
* value_MPI_IN_PLACE = 1
* size_MPI_IN_PLACE = 8

## 1.10.2

* value_MPI_BOTTOM = 0
* size_MPI_BOTTOM = 8
* value_MPI_IN_PLACE = 1
* size_MPI_IN_PLACE = 8
(...)
```


