from pycket.prims.linklet import W_Linklet, to_rpython_list, do_compile_linklet, W_LinkletInstance
from pycket.interpreter import check_one_val, Done
from pycket.values import W_Symbol, W_WrappedConsProper, w_null, W_Object, Values, w_false, w_true, W_Path, W_ThreadCell
from pycket.values_string import W_String
from pycket.vector import W_Vector
from pycket.expand import JsonLoader
from pycket.util import console_log
from pycket.prims.correlated import syntax_primitives

def locate_linklet(file_name):
    import os
    from pycket.error import SchemeException

    env_vars = os.environ.keys()
    if "PYTHONPATH" not in env_vars:
        raise SchemeException("For PyPy to work with Pycket, PYTHONPATH variable should be set in the environment.. See README")

    python_path = os.environ["PYTHONPATH"]
    py_paths = python_path.split(':')

    file_path = ""
    for p in py_paths:
        f_path = os.path.join(p, file_name)
        if os.path.exists(f_path):
            file_path = f_path
            break
        # Also try the UP (since PYTHONPATH may only point to the PyPy)
        up_file = os.path.join(p, "../" + file_name)
        if os.path.exists(up_file):
            file_path = up_file
            break
    else:
        raise SchemeException("Can't locate the : %s" % file_name)

    return file_path

def load_bootstrap_linklets(pycketconfig, debug=False):

    console_log("Loading the expander linklet...")
    expander_file_path = locate_linklet("expander.rktl.linklet")

    # load the expander linklet
    expander_instance, sys_config = load_inst_linklet_json(expander_file_path, pycketconfig, debug)
    expander_instance.provide_all_exports_to_prim_env(excludes=syntax_primitives)

    console_log("Expander loading complete.")

    return sys_config

def load_inst_linklet_json(json_file_name, pycketconfig, debug=False):

    console_log("Loading linklet from %s" % json_file_name)
    linkl, sys_config = W_Linklet.load_linklet(json_file_name, JsonLoader())

    console_log("Instantiating %s ...."  % json_file_name)
    instantiate_linklet = get_primitive("instantiate-linklet")
    linkl_instance = instantiate_linklet.call_interpret([linkl, w_null, w_false, w_false], pycketconfig)
    console_log("DONE.")
    return linkl_instance, sys_config

def set_path(kind_str, path_str):
    import os
    from pycket.racket_paths import racket_sys_paths

    if not os.path.exists(path_str):
        raise Exception("File not found : %s" % path_str)

    racket_sys_paths.set_path(W_Symbol.make(kind_str), W_Path(path_str))

def initiate_boot_sequence(pycketconfig, command_line_arguments, use_compiled, debug=False, set_run_file="", set_collects_dir="", set_config_dir="", set_addon_dir=""):
    from pycket.env import w_version

    sysconfig = load_bootstrap_linklets(pycketconfig, debug)

    v = sysconfig["version"]
    console_log("Setting the version to %s" % v)
    w_version.set_version(v)

    # These need to be set before the boot sequence
    if set_run_file:
        console_log("Setting the 'run-file path to %s" % set_run_file)
        set_path("run-file", set_run_file)

    if set_collects_dir:
        console_log("Setting the 'collects-dir path to %s" % set_collects_dir)
        set_path("collects-dir", set_collects_dir)

    if set_config_dir:
        console_log("Setting the 'config-dir path to %s" % set_config_dir)
        set_path("config-dir", set_config_dir)

    if set_addon_dir:
        console_log("Setting the 'addon-dir path to %s" % set_addon_dir)
        set_path("addon-dir", set_addon_dir)

    # Set the cmd arguments for racket
    ccla = get_primitive("current-command-line-arguments")
    ccla.call_interpret([W_Vector.fromelements(command_line_arguments)], pycketconfig)

    # Run "boot" to set things like (current-module-name-resolver) (o/w it's going to stay as the
    # "core-module-name-resolver" which can't recognize modules like 'racket/base (anything other than
    # things like '#%kernel really)

    console_log("Entering Boot Sequence")

    console_log("(boot)")
    boot = get_primitive("boot")
    boot.call_interpret([], pycketconfig)

    console_log("(current-library-collection-links (find-library-collection-links))")
    flcl = get_primitive("find-library-collection-links")
    lib_coll_links = flcl.call_interpret([], pycketconfig)
    clcl = get_primitive("current-library-collection-links")
    clcl.call_interpret([lib_coll_links], pycketconfig)

    console_log("(current-library-collection-paths (find-library-collection-paths))")
    flcp = get_primitive("find-library-collection-paths")
    lib_coll_paths = flcp.call_interpret([], pycketconfig)
    clcp = get_primitive("current-library-collection-paths")
    clcp.call_interpret([lib_coll_paths], pycketconfig)

    console_log("(read-accept-compiled true)")
    read_accept_compiled = get_primitive("read-accept-compiled")
    read_accept_compiled.call_interpret([w_true], pycketconfig)

    compiled_file_path = "pycket-compiled"
    ucfp = get_primitive("use-compiled-file-paths")
    if use_compiled:
        console_log("(use-compiled-file-paths %s)" % compiled_file_path)
        ucfp.call_interpret([W_WrappedConsProper.make(W_String.make(compiled_file_path), w_null)], pycketconfig)
    else:
        ucfp.call_interpret([w_null], pycketconfig)
        console_log("(use-compiled-file-paths null)")

    # set the current directory to the current directory
    import os
    c_dir = os.getcwd()
    console_log("(current-directory %s)" % c_dir)
    # We can't call the current-directory like a primitive
    # because it prints a report to stdout
    from pycket.values_parameter import top_level_config
    from pycket.prims.general import current_directory_param
    c = top_level_config.get(current_directory_param)
    assert isinstance(c, W_ThreadCell)
    c.set(W_Path(c_dir))

    console_log("...Boot Sequence Completed")

    return 0

# temporary
def namespace_require_kernel(pycketconfig):

    namespace_require = get_primitive("namespace-require")

    kernel = W_WrappedConsProper.make(W_Symbol.make("quote"),
                                      W_WrappedConsProper.make(W_Symbol.make("#%kernel"), w_null))
    namespace_require.call_interpret([kernel], pycketconfig)

def racket_entry(names, config, pycketconfig, command_line_arguments):

    loads, init_library, is_repl, no_lib, set_run_file, set_collects_dir, set_config_dir, set_addon_dir, just_kernel, debug, version, just_init, use_compiled = get_options(names, config)

    initiate_boot_sequence(pycketconfig, command_line_arguments, use_compiled, debug, set_run_file, set_collects_dir, set_config_dir, set_addon_dir)

    if just_init:
        return 0

    namespace_require = get_primitive("namespace-require")
    load = get_primitive("load")

    if just_kernel:
        console_log("Running on just the #%kernel")
        namespace_require_kernel(pycketconfig)

    if not no_lib:
        init_lib = W_WrappedConsProper.make(W_Symbol.make("lib"),
                                            W_WrappedConsProper.make(W_String.make(init_library), w_null))
        console_log("(namespace-require %s) ..." % init_lib.tostring())

        namespace_require.call_interpret([init_lib], pycketconfig)
        console_log("Init lib : %s loaded..." % (init_library))

    ran_eval = False
    #put_newline = False
    if loads:
        for rator_str, rand_str in loads:
            if rator_str == "load":
                # -f
                console_log("(load %s)" % (rand_str))
                load.call_interpret([W_String.make(rand_str)], pycketconfig)
            elif rator_str == "file" or rator_str == "lib":
                # -t & -l
                load_form = W_WrappedConsProper.make(W_Symbol.make(rator_str),
                                                     W_WrappedConsProper.make(W_String.make(rand_str), w_null))
                console_log("(namespace-require '(%s %s))" % (rator_str, rand_str))
                namespace_require.call_interpret([load_form], pycketconfig)
            elif rator_str == "eval":
                # -e
                ran_eval = True
                console_log("(eval (read (open-input-string %s)))" % rand_str)
                read_eval_print_string(rand_str, pycketconfig, False, debug)

    if version:
        from pycket.env import w_version
        print("Welcome to Pycket v%s" % w_version.get_version())
        
    if is_repl: # -i
        put_newline = True
        dynamic_require = get_primitive("dynamic-require")
        repl = dynamic_require.call_interpret([W_Symbol.make("racket/repl"),
                                               W_Symbol.make("read-eval-print-loop")],
                                              pycketconfig)
        repl.call_interpret([], pycketconfig)

    if is_repl or not ran_eval: #put_newline:
        print

    exit = get_primitive("exit")
    exit.call_interpret([], pycketconfig)

    return 0


def racket_read(input_port, pycketconfig):
    read_prim = get_primitive("read")

    return check_one_val(read_prim.call_interpret([input_port], pycketconfig))

def racket_read_str(expr_str, pycketconfig):
    ois = get_primitive("open-input-string")

    str_port = check_one_val(ois.call_interpret([W_String.make(expr_str)], pycketconfig))

    return racket_read(str_port, pycketconfig)

def racket_read_file(file_name, pycketconfig):
    oif = get_primitive("open-input-file")

    in_port = oif.call_interpret([W_String.make(file_name)], pycketconfig)

    return racket_read(in_port, pycketconfig)

def racket_eval(sexp, pycketconfig):
    eval_prim = get_primitive("eval")
    return eval_prim.call_interpret([sexp], pycketconfig)

def racket_expand(sexp, pycketconfig):
    ex = get_primitive("expand")
    return check_one_val(ex.call_interpret([sexp], pycketconfig))

def racket_print(results, pycketconfig):
    pr = get_primitive("print")

    if isinstance(results, W_Object):
        # print single
        pr.call_interpret([results], pycketconfig)
        pr.call_interpret([W_String.make("\n")], pycketconfig)
    elif isinstance(results, Values):
        # print multiple values
        for r in results.get_all_values():
            pr.call_interpret([r], pycketconfig)
            pr.call_interpret([W_String.make("\n")], pycketconfig)
    else:
        raise Exception("Unsupoorted result value : %s" % results.tostring())

def read_eval_print_string(expr_str, pycketconfig, return_val=False, debug=False):
    # read
    sexp = racket_read_str(expr_str, pycketconfig)

    # expand
    #expanded = racket_expand(sexp, pycketconfig)

    # eval
    results = racket_eval(sexp, pycketconfig)

    if return_val:
        return results

    # print
    racket_print(results, pycketconfig)

    # FIXME
    console_log("(print (eval (read (open-input-string %s))))" % (expr_str))
    return 0

def get_primitive(prim_name_str):
    from pycket.prims.expose import prim_env
    from pycket.error import SchemeException

    prim_sym = W_Symbol.make(prim_name_str)
    if not prim_sym in prim_env:
        raise SchemeException("Primitive not found : %s" % prim_name_str)

    return prim_env[prim_sym]

def get_options(names, config):

    load_rators = names['loads'] if 'loads' in names else []
    load_rands = names['load_arguments'] if 'load_arguments' in names else []
    set_run_file = names['set-run-file'][0] if 'set-run-file' in names else ""
    set_collects_dir = names['set-collects-dir'][0] if 'set-collects-dir' in names else ""
    set_config_dir = names['set-config-dir'][0] if 'set-config-dir' in names else ""
    set_addon_dir = names['set-addon-dir'][0] if 'set-addon-dir' in names else ""

    init_library = names['init-lib'][0] if 'init-lib' in names else "racket/kernel/init" # racket/init
    is_repl = config['repl']
    no_lib = config['no-lib']
    just_kernel = config['just_kernel']
    just_init = config['just-init']
    use_compiled = config['use-compiled']
    debug = config['verbose']
    version = config['version']

    loads_print_str = []
    loads = []
    for index, rator in enumerate(load_rators):
        rand = load_rands[index]
        loads_print_str.append("(%s %s)" % (rator, rand))
        loads.append([rator, rand])

    log_str = """Options :

loads            : %s
set-run-file     : %s
set-collects-dir : %s
set-config-dir   : %s
set-addon-dir    : %s
init_library     : %s
is_repl          : %s
no_lib           : %s
just-#%%kernel    : %s
just-init        : %s
use-compiled     : %s
""" % (loads_print_str,
       set_run_file,
       set_collects_dir,
       set_config_dir,
       set_addon_dir,
       init_library,
       is_repl,
       no_lib,
       just_kernel,
       just_init,
       use_compiled)

    console_log(log_str)

    return loads, init_library, is_repl, no_lib, set_run_file, set_collects_dir, set_config_dir, set_addon_dir, just_kernel, debug, version, just_init, use_compiled
