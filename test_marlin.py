# -*- coding: utf-8 -*-

import marlin


def test_corpora():
    assert marlin.Corpus("syn2015").name == "syn2015"
    assert marlin.Corpus("oral2013").name == "oral2013"


def test_normalize_cql():
    norm = marlin.Corpus._normalize_cql
    test = norm('[ lemma=  "foo bar baz" ] ')
    assert test == '[lemma="foo bar baz"]' and type(test) is unicode
    test = norm('"foo"   "bar"  "b az"')
    assert test == '"foo""bar""b az"' and type(test) is unicode
    test = norm(u' [lemma="kočka" ]')
    assert test == u'[lemma="kočka"]' and type(test) is unicode


def test_simple_query():
    squery = marlin.Corpus._simple_query
    test = squery(u"kočka")
    assert test == u'[lemma="(?i)kočka"|word="(?i)kočka"]' and type(test) is unicode


def test_getting_num_of_positions_per_value_of_structural_attribute():
    corp = marlin.Corpus("syn2010")
    tpa = corp.toks_per_attrval("opus.txtype")
    assert tpa["IMA"] == 347012
