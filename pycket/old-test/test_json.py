
import pytest
from pycket.pycket_json import loads
import json as pyjson

def _compare(string, expected):
    json = loads(string)
    val = json._unpack_deep()
    assert val == expected
    #assert val == pyjson.loads(string)

def test_simple():
    _compare("1", 1)
    _compare("\"abc\"", "abc")
    _compare("1.2", 1.2)

def test_array():
    _compare("[]", [])
    _compare("[1]", [1])
    _compare("[1, 2.0, 3.0, \"abc\", [10.0, \"def\"]]", [1, 2.0, 3.0, "abc", [10.0, "def"]])

def test_object():
    _compare("{}", {})
    _compare("{\"a\": 1}", {"a": 1})
    _compare("{\"a\": 1, \"123\": \"ab\", \"subobj\": {\"d\": 12.0}, \"subarr\": [1]}", {"a": 1, "123": "ab", "subobj": {"d": 12.0}, "subarr": [1]})

def test_escaped_string():
    _compare('"\\n"', "\n")
    _compare('"\\n\\t\\b\\f\\r\\\\"', "\n\t\b\f\r\\")
    _compare('"\\n\\t\\b\\f\\r\\\\"', "\n\t\b\f\r\\")
    _compare('["\\\\"]', ["\\"])
    _compare('["\\\\\\\\"]', ["\\\\"])
    _compare('"\\""', '"')

def test_tostring_string_escaping():
    json = loads('"\\n"')
    assert json.tostring() == '"\\n"'

def test_bug():
    # Lexer was having issues with single backslashes which would allow the string
    # production rule to continue consuming past the end of a string
    _compare(r'{"string" : "\\"}', {"string": "\\"})
    _compare(r'[{ "quote": { "string": "\\" } },{ "quote": { "string": "Hi" } }]',
            [{"quote" : { "string": "\\" }},{"quote" : { "string": "Hi" }}])

    _compare(r'{"string" : "\\\\"}', {"string": "\\\\"})
