#! /usr/bin/env python
# -*- coding: utf-8 -*-
#
# _____ Define and setup target ___

from rpython.rlib import jit, objectmodel

POST_RUN_CALLBACKS = []

def register_post_run_callback(callback):
    """
    Registers functions to be called after the user program terminates.
    This is mostly useful for defining debugging/logging hooks to print out
    runtime stats after the program is done.
    """
    POST_RUN_CALLBACKS.append(callback)
    return callback

@register_post_run_callback
def save_callgraph(config, env):
    if config.get('save-callgraph', False):
        with open('callgraph.dot', 'w') as outfile:
            env.callgraph.write_dot_file(outfile)

def make_entry_point(pycketconfig=None):
    from pycket.interpreter import ToplevelEnv
    from pycket.error import SchemeException, ExitException
    from pycket.option_helper import parse_args
    from pycket.values_string import W_String
    from pycket.racket_entry import load_inst_linklet_json, racket_entry

    def entry_point(argv):
        if not objectmodel.we_are_translated():
            import sys
            sys.setrecursionlimit(10000)
        try:
            return actual_entry(argv)
        except SchemeException, e:
            print "ERROR:"
            print e.format_error()
            raise # to see interpreter-level traceback

    def actual_entry(argv):
        jit.set_param(None, "trace_limit", 1000000)
        jit.set_param(None, "threshold", 131)
        jit.set_param(None, "trace_eagerness", 50)
        jit.set_param(None, "max_unroll_loops", 15)

        from pycket.env import w_global_config
        w_global_config.set_pycketconfig(pycketconfig)

        config, names, args, retval = parse_args(argv)

        if config['verbose']:
            level = int(names['verbosity_level'][0])
            w_global_config.set_config_val('verbose', level)

            if 'not-implemented' in names:
                print("These flags are not implemented yet : %s" % names['not-implemented'])

        if 'stdout_level' in names: # -O
            from pycket.prims.logging import w_main_logger
            w_main_logger.set_stdout_level(names['stdout_level'][0])

        if 'stderr_level' in names: # -W
            from pycket.prims.logging import w_main_logger
            w_main_logger.set_stderr_level(names['stderr_level'][0])

        if 'syslog_level' in names: # -L
            from pycket.prims.logging import w_main_logger
            w_main_logger.set_syslog_level(names['syslog_level'][0])

        if retval != 0 or config is None:
            return retval

        current_cmd_args = [W_String.fromstr_utf8(arg) for arg in args]

        if 'json-linklets' in names:
            for linkl_json in names['json-linklets']:
                vvv = config['verbose']
                load_inst_linklet_json(linkl_json, pycketconfig, vvv)

        try:
            if not config['stop']:
                racket_entry(names, config, pycketconfig, current_cmd_args)
        except ExitException, e:
            pass
        finally:
            from pycket.prims.input_output import shutdown
            env = ToplevelEnv(pycketconfig)
            #env.commandline_arguments = current_cmd_args
            for callback in POST_RUN_CALLBACKS:
                callback(config, env)
            shutdown(env)
        return 0
    return entry_point

def target(driver, args): #pragma: no cover
    from rpython.config.config import to_optparse
    from pycket.config import expose_options, compute_executable_suffix
    config = driver.config
    parser = to_optparse(config, useoptions=["pycket.*"])
    parser.parse_args(args)
    if config.pycket.with_branch:
        import subprocess
        base_name = subprocess.check_output(["git", "rev-parse", "--abbrev-ref", "HEAD"]).strip()
    else:
        base_name = 'pycket'
    base_name += '-%(backend)s'
    if not config.translation.jit:
        base_name += '-%(backend)s-nojit'

    driver.exe_name = base_name + compute_executable_suffix(config)
    # it's important that the very first thing we do, before importing anything
    # else from pycket is call expose_options
    expose_options(config)
    entry_point = make_entry_point(config)
    return entry_point, None

def get_additional_config_options(): #pragma: no cover
    from pycket.config import pycketoption_descr
    return pycketoption_descr

take_options = True
