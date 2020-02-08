# -*- coding: utf-8 -*-
from __future__ import division

import os
import hashlib
from itertools import izip

from flask import Flask, abort, render_template
from flask_turbolinks import turbolinks
from flask_wtf import Form
from wtforms import IntegerField, SelectField, StringField, TextAreaField
import wtforms.validators as validators

import re
import manatee

app = Flask("marlin")

# CONFIG
app.config.update(
    SECRET_KEY="a random string",
    DEFAULT_CORPUS="test",
    CACHE_DIR=os.path.abspath(".cache"),
    MANATEE_REGISTRY="/corpora/registry",
)
app = turbolinks(app)
os.environ["MANATEE_REGISTRY"] = app.config["MANATEE_REGISTRY"]
if not os.path.isdir(app.config["CACHE_DIR"]):
    os.makedirs(app.config["CACHE_DIR"])


def find_corpora(registry):
    corpora = set()
    for dirpath, _, filenames in os.walk(registry):
        for name in filenames:
            with open(os.path.join(dirpath, name)) as fh:
                try:
                    line = fh.readline().strip()
                    prop, _ = re.split(r"\s+", line, 1)
                # split unsuccessful
                except ValueError:
                    continue
            if prop == "NAME":
                corpora.add(name)
    return sorted(corpora)


app.config["CORPORA"] = find_corpora(app.config["MANATEE_REGISTRY"])


class Corpus(object):
    """A wrapper for manatee corpora.

    """

    def __init__(self, corpname):
        self._corpus = manatee.Corpus(corpname)
        self.enc = self._corpus.get_conf("ENCODING")
        self.name = corpname

    def __getattr__(self, attr):
        return getattr(self._corpus, attr)

    def __repr__(self):
        name = self.name.encode("unicode-escape")
        return "<Corpus {}>".format(name)

    @staticmethod
    def _simple_query(query):
        query = re.sub(r'(["\*\+\-\.\\\[\]\(\)\{\}])', r"\\1", query)
        cql = u""
        for tok in query.split():
            cql += u'[lemma="(?i){0}"|word="(?i){0}"]'.format(tok)
        return cql

    @staticmethod
    def _normalize_cql(cql):
        # make sure cql doesn't start with a "
        cql = u" " + cql
        cqlist = re.split(r'(?<!\\)"', cql)
        cql = u""
        for i, span in enumerate(cqlist):
            # span outside quotes, normalize it
            if i % 2 == 0:
                # split again at spaces between two word characters, because we
                # need to keep those
                span_list = re.split(r"(?<=\w)\s+(?=\w)", span)
                for j in range(len(span_list)):
                    # kill all other whitespace
                    span_list[j] = re.sub(r"\s+", "", span_list[j])
                # restore (normalized) whitespace between word chars
                cql += " ".join(span_list)
            # span belongs inside quotes, leave it alone
            else:
                cql += u'"' + span + u'"'
        return cql

    def query(self, cql, shuffle=True):
        """Run query on corpus.

        :param cql: A CQL query string. If parsing fails, it is interpreted as
        a simple query.

        """
        # see if the CQL is valid
        try:
            Concordance(self, cql)
        # if the query fails to compile, then just interpret it as a list of
        # lemmas/forms
        except RuntimeError:
            cql = self._simple_query(cql)
        # normalize CQL to optimize caching
        cql = self._normalize_cql(cql)
        return self._query(cql, shuffle)

    def check_cache(self, cql):
        bytestring = (self.name + cql).encode("utf-8")
        conc_hash = hashlib.md5(bytestring).hexdigest()
        cache_path = os.path.join(app.config["CACHE_DIR"], conc_hash + ".conc")
        if os.path.exists(cache_path):
            return cache_path, True
        else:
            return cache_path, False

    def _query(self, cql, shuffle):
        cache_path, cache_exists = self.check_cache(cql)
        if cache_exists:
            log = u"Found cache file {}\n  for corpus {}\n  and query {}."
            app.logger.debug(log.format(cache_path, self.name, cql))
            # read and return cache
            return CachedConcordance(cache_path, self, cql)
        conc = Concordance(self, cql)
        # this is fairly time-consuming for large concordances
        conc.sync()
        # and this even more
        if shuffle:
            conc.shuffle()
        conc.save(cache_path, False, False, False)
        return conc

    def toks_per_attrval(self, struct_attr):
        struct, attr = struct_attr.split(".")
        struct = self.get_struct(struct)
        attr = struct.get_attr(attr)
        struct_len_at_pos = {
            struct.beg(i): struct.end(i) - struct.beg(i) for i in range(struct.size())
        }
        ans = {}
        for attrid in range(attr.id_range()):
            attrval = attr.id2str(attrid)
            rs = self.filter_query(struct.attr_val(attr.name, attrid))
            length = 0
            while not rs.end():
                length += struct_len_at_pos[rs.peek_beg()]
                rs.next()
            ans[attrval.decode(self.enc)] = length
        return ans


class Concordance(object):
    """A wrapper for manatee concordances.

    """

    def __init__(self, corpus, cql, sample_size=0, result_size=-1):
        self.corpus = corpus
        self.cql = cql
        self._conc = manatee.Concordance(
            corpus._corpus, cql.encode(corpus.enc), sample_size, result_size
        )

    def __getattr__(self, attr):
        return getattr(self._conc, attr)

    def __repr__(self):
        corpus = self.corpus.name.encode("unicode-escape")
        query = self.cql.encode("unicode-escape")
        return "<{} Concordance for {}>".format(corpus, query)

    def kwic_lines(self, lctx, rctx, kwic_attrs, ctx_attrs, structs, meta, max_ctx):
        lctx, rctx = str(lctx), str(rctx)
        return manatee.KWICLines(
            self.corpus._corpus,
            self._conc.RS(True),
            lctx,
            rctx,
            kwic_attrs,
            ctx_attrs,
            structs,
            meta,
            max_ctx,
        )


class CachedConcordance(Concordance):
    def __init__(self, cache_file, corpus, cql):
        self.corpus = corpus
        self.cql = cql
        self._conc = manatee.Concordance(corpus._corpus, cache_file)


class QueryForm(Form):
    corpora = app.config["CORPORA"]
    # watch out, choices need to be zipped, not izipped, because they're
    # consumed each time a form is created, and a generator remains empty once
    # spent
    corpus = SelectField(
        u"Corpus name", [validators.required()], choices=zip(corpora, corpora)
    )
    cql = TextAreaField(
        u"Simple query (bare words / lemmas) or CQL", [validators.required()]
    )


class FreqDistForm(Form):
    by = StringField(u"Grouping attribute", [validators.required()])
    # default="word")
    offset = IntegerField(u"Offset from KWIC", [validators.required()])
    # default=0)
    minfreq = IntegerField(u"Minimum frequency", [validators.required()])
    # default=0)


def create_forms(kwargs):
    forms = {}
    forms["query"] = QueryForm(corpus=kwargs.get("corpus"), cql=kwargs.get("cql"))
    forms["def_corp"] = kwargs.get("corpus", app.config["DEFAULT_CORPUS"])
    forms["freq_dist"] = FreqDistForm(
        by=kwargs.get("by", "word"),
        offset=kwargs.get("offset", 0),
        minfreq=kwargs.get("minfreq", 0),
    )
    return forms


def freq_info(corpus, conc):
    abs = conc.size()
    ipm = abs / corpus.size() * 1e6
    arf = conc.compute_ARF()
    return locals()


def as_unicode(str_tuple, enc):
    if len(str_tuple) > 2 or not str_tuple[1].startswith("{"):
        raise RuntimeError("Inspect ``str_tuple``.")
    return str_tuple[0].decode(enc)


def pager(conc, per_page, current):
    prev = current - 1 if current > 1 else None
    next = current + 1 if current * per_page < conc.size() else None
    return locals()


@app.route("/")
def index():
    return render_template("conc.html", forms=create_forms(locals()))


# the cql parameter must use a path converter because it might contain slashes
# (even though they'll be encoded)
@app.route("/conc/<corpus>/<path:cql>/<int:page>")
def conc(corpus, cql, page):
    forms = create_forms(locals())
    try:
        corpus = Corpus(corpus)
    except manatee.CorpInfoNotFound:
        abort(404, "Invalid corpus name.")
    conc = corpus.query(cql)
    kwic_lines = conc.kwic_lines(-15, 15, "word", "word", "", "=doc.id", 0)
    enc = corpus.enc
    per_page = 50
    kwic_lines.skip((page - 1) * per_page)
    result = []
    i = 0
    while kwic_lines.nextline() and i < per_page:
        meta = kwic_lines.get_refs().decode(enc)
        left = as_unicode(kwic_lines.get_left(), enc)
        kwic = as_unicode(kwic_lines.get_kwic(), enc)
        right = as_unicode(kwic_lines.get_right(), enc)
        result.append((meta, left, kwic, right))
        i += 1
    return render_template(
        "conc.html",
        forms=forms,
        conc=result,
        freq=freq_info(corpus, conc),
        def_corp=corpus.name,
        pager=pager(conc, per_page, page),
        real_query=conc.cql,
    )


def freq_dist_ipms(items, freqs, norms, corpsize):
    def _ipm(item, freq):
        if type(norms) == dict:
            return freq / norms[item] * 1e6
        else:
            return freq / corpsize * 1e6

    return [_ipm(item, freq) for (item, freq) in izip(items, freqs)]


@app.route("/freq/<corpus>/<cql>/<by>/<int:offset>/<int:minfreq>")
def freq(corpus, cql, by, offset, minfreq):
    forms = create_forms(locals())
    how = "{}/ {}<{}".format(by, offset, minfreq)
    items = manatee.StrVector()
    freqs = manatee.NumVector()
    norms = manatee.NumVector()
    try:
        corpus = Corpus(corpus)
    except manatee.CorpInfoNotFound:
        abort(404, "Invalid corpus name.")
    conc = corpus.query(cql)
    corpus.freq_dist(conc.RS(), how, 0, items, freqs, norms)
    items = map(lambda x: x.decode(corpus.enc), items)
    # throw away manatee's norms if computed, like KonText does (what do they
    # mean anyway??)
    if sum(norms) > 0:
        norms = corpus.toks_per_attrval(by)
    ipms = freq_dist_ipms(items, freqs, norms, corpus.size())
    rows = zip(items, freqs, ipms)
    # if the freq dist is long, take only the first 10000 items (the rest are
    # useless anyway); TODO: notify user of this
    rows = rows[:1e4] if len(rows) > 1e4 else rows
    return render_template(
        "freq.html",
        forms=forms,
        def_corp=corpus.name,
        rows=rows,
        abs_max=max(freqs),
        ipm_max=max(ipms),
    )


if __name__ == "__main__":
    app.run(debug=True, host="::", port=1993)
