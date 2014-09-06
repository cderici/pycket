#! /usr/bin/env python
# -*- coding: utf-8 -*-
from ..      import impersonators as imp
from ..      import values
from ..cont  import get_mark_first
from ..error import SchemeException
from .expose import default, expose, make_callable_label

# Can use this to promote a get_cmk operation to a callable function.
CMKSetToListHandler = make_callable_label([values.W_Object])

#@expose("continuation-marks",
        #[values.W_Continuation, default(values.W_ContinuationPromptTag, None)])
#def continuation_marks(cont, prompt_tag):
    #return values.W_ContinuationPromptTag(cont.cont)

@expose("current-continuation-marks", [default(values.W_ContinuationPromptTag, None)], simple=False)
def current_cont_marks(prompt_tag, env, cont):
    from ..interpreter import return_value
    return return_value(values.W_ContinuationMarkSet(cont), env, cont)

@expose("continuation-mark-set->list",
        [values.W_ContinuationMarkSet, values.W_Object], simple=False)
def cms_list(cms, mark, env, cont):
    from ..interpreter import return_value
    from .general      import map_loop
    if isinstance(mark, values.W_ContinuationMarkKey):
        func  = CMKSetToListHandler(mark.get_cmk)
        marks = cms.cont.get_marks(imp.get_base_object(mark))
        return map_loop(func, [marks], env, cont)
    marks = cms.cont.get_marks(mark)
    return return_value(marks, env, cont)

@expose("continuation-mark-set-first", [values.W_Object, values.W_Object, default(values.W_Object, values.w_false)], simple=False)
def cms_list(cms, mark, missing, env, cont):
    from ..interpreter import return_value
    if cms is values.w_false:
        the_cont = cont
    elif isinstance(cms, values.W_ContinuationMarkSet):
        the_cont = cms.cont
    else:
        raise SchemeException("Expected #f or a continuation-mark-set")
    is_cmk = isinstance(mark, values.W_ContinuationMarkKey)
    m = imp.get_base_object(mark) if is_cmk else mark
    v = get_mark_first(the_cont, m)
    val = v if v is not None else missing
    if is_cmk:
        return mark.get_cmk(val, env, cont)
    return return_value(val, env, cont)

@expose("make-continuation-mark-key", [default(values.W_Symbol, None)])
def mk_cmk(s):
    from ..interpreter import Gensym
    s = Gensym.gensym("cm") if s is None else s
    return values.W_ContinuationMarkKey(s)
