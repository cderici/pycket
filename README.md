[![Build Status](https://travis-ci.org/pycket/pycket.png?branch=master)](https://travis-ci.org/cderici/pycket)
[![codecov.io](https://codecov.io/github/pycket/pycket/coverage.svg?branch=master)](https://codecov.io/github/pycket/pycket?branch=master)

Pycket is a Racket/Scheme implementation that is automatically
generated using the [RPython
framework](https://rpython.readthedocs.io/en/latest/). Given an
interpreter written in RPython (in our case a CEK machine interpreter
for Racket), RPython framework produces a fast binary for
it. It can also add a tracing JIT.

There are currently two different modes of evaluation that we refer as
`OLD` and `NEW`. The `NEW` Pycket uses `linklets` and bootstraps the
Racket using the `expander` linklet exported by Racket (version
7+). The `OLD` Pycket, on the other hand, uses Racket's binary to
fully expand the program and generates `json` asts and evaluates them.

Note that both versions require an unmodified Racket installation. The
`OLD` Pycket requires a Racket binary, and while the `NEW` Pycket
doesn't require a Racket binary, it still requires the Racket packages
and libraries to bootstrap.

## Building

In order to do anything with Pycket, you need to check out PyPy:

    $ hg clone https://bitbucket.org/pypy/pypy

The below instructions assume that you do this checkout in Pycket's directory.

Additionally, it helps to have the build dependencies of PyPy installed.
On a Debian or Ubuntu system:

    $ sudo apt-get build-dep pypy

To produce an executable, run:

    $ ./pypy/rpython/bin/rpython -Ojit targetpycket.py

This expects that a binary named `pypy` is in your path. (Note that
a hand-compiled PyPy by running `make` produces `pypy-c`, not `pypy`).

If you don't have a PyPy binary, you can also translate with the CPython:

    $ python ./pypy/rpython/bin/rpython -Ojit targetpycket.py

This will take upwards of 10 minutes.

## Make Targets

You can also use `make` for any of the above,

 * `make setup` to setup and update the `pypy` checkout and install `pycket-lang` to Racket
 * `make test` to run the unit tests
 * `make expander` to generate the expander linklet (it assumes an unmodified Racket install and PLTHOME environment variable -- see the Environment Variables section below)
 * `make pycket-c` to translate with JIT
 * `make pycket-c-nojit` to translate without JIT (which may be a lot faster to translate but runs a lot lot slower)

## Using Compiled Files

The `NEW` Pycket is able to generate and use its own `.zo` files. For
now both the generation and the use are manual.

To generate a `.zo` file for a `.rkt` source file, use `make
compile-file`:

    $ make compile-file FILE=$(PLTHOME)/racket/collects/racket/private/qq-and-or.rkt

The parameter that enables Racket expander to use compiled code is
`use-compiled-file-paths`, which defaults to `pycket-compiled` in
Pycket. Whenever a module is required, the expander will use the
compiled code if it exists, otherwise it will use the source code of
the module (read, expand, etc.).

    pycket-repl> (#%require racket/private/qq-and-or)

Note that `pycket-compiled` is a folder that `make compile-file` is
going to generate by itself.

This is a work in progress. We plan to have a make target that
pre-compiles all the Racket modules automatically by following the
module dependencies. Currently, the modules need to be compiled one by
one.

## Environment Variables

Running the interpreter on CPython or PyPy (i.e. running the
targetpycket.py) requires a `PYTHONPATH` that includes both `RPython`
(that should be the `pypy` directory cloned above) and `pycket` (that
should be this directory).

Also there are a couple of variables need to be set for the `NEW`
Pycket to interact with the Racket, since it bootstraps Racket by
reading and evaluating Racket's main collection by loading and using
the bootstrap linklets (currently only the `expander.rktl.linklet`)
exported by Racket. So the `NEW` Pycket needs to be able to locate
various different parts of the Racket installation. The `OLD` Pycket
is lucky to use the Racket's own binary.

Naturally, it varies on the way in which the Racket is installed:

### If Racket is installed in a single directory (non-Unix-style) :

Then all the `NEW` Pycket needs is a `PLTHOME` environment variable to
point to the surrounding directory. For example it will assume the
`collects` directory is at:

> $PLTHOME/racket/collects

### If Racket is installed in Unix-style :

Then `NEW` Pycket needs to know the locations of various
directories. In particular, it needs:

 * `PLTEXECFILE` to point to the location of the `racket` binary
 * `PLTCOLLECTS` to point to the `collects` directory for the main
collections 
 * `PLTCONFIGDIR` to point to Racket's `etc` directory that contains
`config.rktd`
 * (optional) `PLTADDONDIR` to point to a directory for user-specific
Racket configuration, packages, and extensions. It defaults to
`.racket` in USERHOME.
 * (optional) `PLTUSERHOME` to point to the `home` directory of the
  user. It's optional since Pycket will also look at other environment
  variables to figure out the home directory (e.g. `$HOME`).

You can also use the command line options to provide these paths,
e.g. `-X`, `-G` etc.. Run it with `-h` to see all the commands and
options.

    $ ./pycket-c --new -h

Also, the `Makefile` reacts to some variables:
 * `PYPYPATH` for when your `pypy` checkout is not in this directory.   
    Defaults to `pypy`.
 * `PYTEST` for when you don’t want to use `pypy`’s version of pytest.  
    Defaults to `$(PYPYPATH)/pytest.py`.

 * `RPYTHON` for when you want to use something other than the default
   `rpython` script, but you probably would not want that.  
   Defaults to `$(PYPYPATH)/rpython/bin/rpython --batch`.

## Running

Pycket currently defaults to the `OLD` Pycket. To use the `NEW`
version with the linklets, run it with:

    $ ./pycket-c --new <arguments>

You can run with the `-h` option to see the different command line
options for each versions:

    $ ./pycket-c -h

    $ ./pycket-c --new -h

You can run `pycket-c` like the `racket` binary:

    $ ./pycket-c program.rkt

You can also run pycket under plain python (or `pypy` if its
available), like this:

    $ ./pycket-slow.sh program

## Benchmarking

Pycket's benchmarks are available at [this
repository](https://github.com/krono/pycket-bench), along with
instructions for running them.

## Deprecated Stuff Below -- Will be revised 
   
Or even this, when this directory is in your `PYTHONPATH`:

    $ python -mpycket program

You can edit the shell script to make it use pypy, if desired.

## Misc

You can generate a coverage report with `pytest`:

    $ pypy/pytest.py --cov .

or via

    $ make coverage
    
which also generates an HTML report in `pycket/test/coverage_report`.  
You need these Python packages for that to work:
  * `pytest-cov` (provided with the `pypy` checkout)
  * `cov-core` and `coverage`