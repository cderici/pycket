#! /usr/bin/env python
# -*- coding: utf-8 -*-
#
from rpython.rlib import jit

def print_help(argv):
    print """Welcome to Pycket.
%s [<option> ...] <argument> ...
 File and expression options:
  -e <exprs>, --eval <exprs>         : Evaluate <exprs>, prints results
  -f <file>, --load <file>           : Like -e '(load "<file>")' without printing
  -t <file>, --require <file>        : Like -e '(require (file "<file>"))'
  -l <path>, --lib <path>            : Like -e '(require (lib "<path>"))'
  -p <package>                    ***: Like -e '(require (planet "<package>")'
  -r <file>, --script <file>         : Same as -f <file> -N <file> --
  -u <file>, --require-script <file> : Same as -t <file> -N <file> --
  -k <n> <m> <p>                  ***: Load executable-embedded code from offset <n> to <p>
  -m, --main                      ***: Call `main' with command-line arguments, print results
  -g <json>, --eval-json <json>      : Load and instantiate a linklet json
  -gg <json>                         : Like -g but stops after instantiating

 Interaction options:
  -i, --repl                         : Run interactive read-eval-print loop; implies -v
  -n, --no-lib                       : Skip `(require (lib "<init-lib>"))' for -i/-e/-f/-r
  -v, --version                      : Show version

 Configuration options:
  -c, --no-compiled                  : Disable loading of compiled files
  -q, --no-init-file              ***: Skip load of ~/.racketrc for -i
  -I <path>                          : Set <init-lib> to <path> (sets language)
  -X <dir>, --collects <dir>         : Main collects at <dir> (or "" disables all)
  -G <dir>, --config <dir>           : Main configuration directory at <dir>
  -A <dir>, --addon <dir>            : Addon directory at <dir>
  -U, --no-user-path              ***: Ignore user-specific collects, etc.
  -R <paths>, --compiled <paths>  ***: Set compiled-file search roots to <paths>
  -C, --cross                     ***: Cross-build mode; save current collects and config as host
  -N <file>, --name <file>           : Sets `(find-system-path 'run-file)' to <file>
  -j, --no-jit                    ***: Disable the just-in-time compiler
  -d, --no-delay                  ***: Disable on-demand loading of syntax and code
  -b, --binary                    ***: Read stdin and write stdout/stderr in binary mode
  -W <levels>, --warn <levels>       : Set stderr logging to <levels>
  -O <levels>, --stdout <levels>     : Set stdout logging to <levels>
  -L <levels>, --syslog <levels>     : Set syslog logging to <levels>
  --kernel                           : ignore everything, only load the #%%kernel (for development purposes)
  --save-callgraph                   : save the jit output

 Meta options:
  --just-init                        : Ignore all parameters, initialize the bootstrap linklets and exit
  --verbose <level>                  : Print the debug logs. <level> : natural number (defaults to 0)
  --jit <jitargs>                    : Set RPython JIT options may be 'default', 'off',
                                       or 'param=value,param=value' list
  --                                 : No argument following this switch is used as a switch
  -h, --help                         : Show this information and exits, ignoring other options
Default options:
 If only an argument is specified, it is loaded and evaluated
""" % (argv[0])

file_expr_opts = ["-e", "--eval",
                  "-f", "--load",
                  "-t", "--require",
                  "-l", "--lib",
                  "-p",
                  "-r", "--script",
                  "-u", "--require-script",
                  "-k",
                  "-m", "--main",
                  "-g", "--eval-json",
                  "-gg"]
inter_opts = ["-i", "--repl",
              "-n", "--no-lib",
              "-v", "--version"]
conf_opts = ["-c", "--no-compiled",
             "-q", "--no-init-file",
             "-I",
             "-X", "--collects",
             "-G", "--config",
             "-A", "--addon",
             "-A", "--addon",
             "-U", "--no-user-path",
             "-R", "--compiled",
             "-C", "--cross",
             "-N", "--name",
             "-j", "--no-jit",
             "-d", "--no-delay",
             "-b", "--binary",
             "-W", "--warn",
             "-O", "--stdout",
             "-L", "--syslog",
             "--kernel",
             "--save-callgraph"]
meta_opts = ["--just-init", "--verbose", "--jit", "-h"]

all_opts = file_expr_opts + inter_opts + conf_opts + meta_opts

INIT = -1
RETURN_OK = 0
MISSING_ARG = 5
JUST_EXIT = 3
RET_JIT = 2

config = {
    'repl' : False,
    'no-lib' : False,
    'version' : False,
    'stop' : False,
    'just_kernel' : False,
    'verbose' : False,
    'just-init' : False,
    'use-compiled' : True
}

def add_name(names, name, val, replace=False):
    if name not in names or replace:
        names[name] = [val]
    else:
        names[name].append(val)

def is_rkt_file(name_str):
    return ".rkt" in name_str

def parse_args(argv):
    names = {
        # 'file': "",
        # 'exprs': "",
    }
    args = []
    retval = INIT
    i = 1
    to = len(argv)
    while i < to:
        if False:
            pass

        elif argv[i] in ["-e", "--eval"]:
            if to <= i + 1 or argv[i+1] in all_opts:
                print "missing argument after %s" % argv[i]
                retval = MISSING_ARG
                break

            i += 1
            add_name(names, 'loads', "eval")
            add_name(names, 'load_arguments', argv[i])
            retval = RETURN_OK

        elif argv[i] in ["-f", "--load", "-r", "--script"]:
            if to <= i + 1 or argv[i+1] in all_opts:
                print "missing argument after %s" % argv[i]
                retval = MISSING_ARG
                break

            i += 1
            add_name(names, 'loads', "load")
            add_name(names, 'load_arguments', argv[i])

            if argv[i-1] in ["-r", "--script"]:
                add_name(names, 'set-run-file', argv[i])

            retval = RETURN_OK

        elif argv[i] in ["-t", "--require", "-u", "--require-script"]:
            if to <= i + 1 or argv[i+1] in all_opts:
                print "missing argument after %s" % argv[i]
                retval = MISSING_ARG
                break

            i += 1
            add_name(names, 'loads', "file")
            add_name(names, 'load_arguments', argv[i])

            if argv[i-1] in ["-u", "--require-script"]:
                add_name(names, 'set-run-file', argv[i])

            config['no-lib'] = True
            retval = RETURN_OK

        elif argv[i] in ["-l", "--lib"]:
            if to <= i + 1 or argv[i+1] in all_opts:
                print "missing argument after %s" % argv[i]
                retval = MISSING_ARG
                break

            i += 1
            add_name(names, 'loads', "lib")
            add_name(names, 'load_arguments', argv[i])

            config['no-lib'] = True
            retval = RETURN_OK

        elif argv[i] in ["-p"]:
            add_name(names, 'not-implemented', argv[i])
            i += 1

        elif argv[i] in ["-k"]:
            add_name(names, 'not-implemented', argv[i])
            i += 3

        elif argv[i] in ["-m", "--main"]:
            add_name(names, 'not-implemented', argv[i])

        elif argv[i] in ["-g", "-gg", "--eval-json"]:
            if argv[i] == "-gg":
                config['stop'] = True
            if to <= i + 1 or argv[i+1] in all_opts:
                print "missing argument after %s" % argv[i]
                retval = MISSING_ARG
                break

            i += 1
            add_name(names, 'json-linklets', argv[i])

            config['no-lib'] = True
            retval = RETURN_OK

        #########################
        # Interaction Options
        #########################

        elif argv[i] in ["-i", "--repl"]:
            config['repl'] = True
            config['version'] = True
            retval = RETURN_OK

        elif argv[i] in ["-n", "--no-lib"]:
            config['no-lib'] = True
            if retval == INIT:
                retval = JUST_EXIT

        elif argv[i] in ["-v", "--version"]:
            config['version'] = True

        #########################
        # Configuration Options
        #########################

        elif argv[i] in ["-c", "--no-compiled"]:
            config['use-compiled'] = False

        elif argv[i] in ["-q", "--no-init-file"]:
            add_name(names, 'not-implemented', argv[i])

        elif argv[i] == "-I":
            if to <= i + 1 or argv[i+1] in all_opts:
                print "missing argument after %s" % argv[i]
                retval = MISSING_ARG
                break
            i += 1
            add_name(names, 'init-lib', argv[i])

        elif argv[i] in ["-X", "--collects"]:
            if to <= i + 1 or argv[i+1] in all_opts:
                print "missing argument after %s" % argv[i]
                retval = MISSING_ARG
                break
            i += 1
            add_name(names, 'set-collects-dir', argv[i])

        elif argv[i] in ["-G", "--config"]:
            if to <= i + 1 or argv[i+1] in all_opts:
                print "missing argument after %s" % argv[i]
                retval = MISSING_ARG
                break
            i += 1
            add_name(names, 'set-config-dir', argv[i])

        elif argv[i] in ["-A", "--addon"]:
            if to <= i + 1 or argv[i+1] in all_opts:
                print "missing argument after %s" % argv[i]
                retval = MISSING_ARG
                break
            i += 1
            add_name(names, 'set-addon-dir', argv[i])

        elif argv[i] in ["-U", "--no-user-path"]:
            add_name(names, 'not-implemented', argv[i])

        elif argv[i] in ["-R", "--compiled"]:
            if to <= i + 1 or argv[i+1] in all_opts:
                print "missing argument after %s" % argv[i]
                retval = MISSING_ARG
                break
            add_name(names, 'not-implemented', argv[i])
            i += 1

        elif argv[i] in ["-C", "--cross"]:
            add_name(names, 'not-implemented', argv[i])

        elif argv[i] in ["-N", "--name"]:
            if to <= i + 1 or argv[i+1] in all_opts:
                print "missing argument after %s" % argv[i]
                retval = MISSING_ARG
                break
            i += 1
            add_name(names, 'set-run-file', argv[i])

        elif argv[i] in ["-j", "--no-jit"]:
            add_name(names, 'not-implemented', argv[i])

        elif argv[i] in ["-d", "--no-delay"]:
            add_name(names, 'not-implemented', argv[i])

        elif argv[i] in ["-b", "--binary"]:
            add_name(names, 'not-implemented', argv[i])

        elif argv[i] in ["-W", "--warn"]:
            if to <= i + 1 or argv[i+1] in all_opts:
                print "missing argument after %s" % argv[i]
                retval = MISSING_ARG
                break
            i += 1
            add_name(names, 'stderr_level', argv[i])

        elif argv[i] in ["-O", "--stdout"]:
            if to <= i + 1 or argv[i+1] in all_opts:
                print "missing argument after %s" % argv[i]
                retval = MISSING_ARG
                break
            i += 1
            add_name(names, 'stdout_level', argv[i])

        elif argv[i] in ["-L", "--syslog"]:
            if to <= i + 1 or argv[i+1] in all_opts:
                print "missing argument after %s" % argv[i]
                retval = MISSING_ARG
                break
            i += 1
            add_name(names, 'syslog_level', argv[i])

        elif argv[i] == "--kernel":
            config['just_kernel'] = True
            config['no-lib'] = True
            retval = RETURN_OK

        elif argv[i] == '--save-callgraph':
            config['save-callgraph'] = True

        #########################
        # Meta Options
        #########################

        elif argv[i] == "--verbose":
            config['verbose'] = True
            add_name(names, 'verbosity_level', '0')
            if to > i + 1 and not is_rkt_file(argv[i+1]) and argv[i+1] not in all_opts:
                vl = argv[i+1]
                if not vl.isdigit() or int(vl) < 0:
                    print("--verbose <level> can only be a natural number, given : %s" % vl)
                    retval = MISSING_ARG
                    break
                add_name(names, 'verbosity_level', vl, replace=True)
                i += 1

        elif argv[i] == "--just-init":
            config['just-init'] = True
            retval = RETURN_OK

        elif argv[i] == "--jit":
            if to <= i + 1:
                print "missing argument after --jit"
                retval = RET_JIT
                break
            i += 1
            jitarg = argv[i]
            jit.set_user_param(None, jitarg)

        elif argv[i] == "--":
            retval = RETURN_OK
            i += 1
            break

        elif argv[i] in ["-h", "--help", "/?", "-?", "/h", "/help"]:
            print_help(argv)
            if retval == INIT:
                retval = JUST_EXIT

        else:
            if '.rkt' in argv[i]:
                add_name(names, 'loads', "file")
                add_name(names, 'load_arguments', argv[i])
                config['no-lib'] = True
                retval = RETURN_OK
            else:
                print "Bad switch : %s" % argv[i]
                retval = MISSING_ARG
        i += 1

    if retval == INIT:
        config['repl'] = True
        config['version'] = True
        retval = RETURN_OK

    if i <= to: #pending args
        args = argv[i:to]

    return config, names, args, retval

# EOF
