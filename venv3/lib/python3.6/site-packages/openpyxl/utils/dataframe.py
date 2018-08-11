from __future__ import absolute_import
# Copyright (c) 2010-2018 openpyxl

import operator
from openpyxl.compat import accumulate, zip


def dataframe_to_rows(df, index=True, header=True):
    """
    Convert a Pandas dataframe into something suitable for passing into a worksheet.
    If index is True then the index will be included, starting one row below the header.
    If header is True then column headers will be included starting one column to the right.
    Formatting should be done by client code.
    """
    import numpy
    from pandas import Timestamp
    blocks = df._data.blocks
    ncols = sum(b.shape[0] for b in blocks)
    data = [None] * ncols

    for b in blocks:
        values = b.values

        if b.dtype.type == numpy.datetime64:
            values = numpy.array([Timestamp(v) for v in values.ravel()])
            values = values.reshape(b.shape)

        result = values.tolist()

        for col_loc, col in zip(b.mgr_locs, result):
            data[col_loc] = col

    if header:
        if df.columns.nlevels > 1:
            rows = expand_levels(df.columns.levels)
        else:
            rows = [list(df.columns.values)]
        for row in rows:
            n = []
            for v in row:
                if isinstance(v, numpy.datetime64):
                    v = Timestamp(v)
                n.append(v)
            row = n
            if index:
                row = [None]*df.index.nlevels + row
            yield row

    cols = None
    if df.index.nlevels > 1:
        cols = zip(*expand_levels(df.index.levels))

    if index:
        yield df.index.names

    for idx, v in enumerate(df.index):
        row = [data[j][idx] for j in range(ncols)]
        if index:
            if cols:
                v = list(next(cols))
            else:
                v = [v]
            row = v + row
        yield row


def expand_levels(levels):
    """
    Multiindexes need expanding so that subtitles repeat
    """
    widths = (len(s) for s in levels)
    widths = list(accumulate(widths, operator.mul))
    size = max(widths)

    for level, width in zip(levels, widths):
        padding = int(size/width) # how wide a title should be
        repeat = int(width/len(level)) # how often a title is repeated
        row = []
        for v in level:
            title = [None]*padding
            title[0] = v
            row.extend(title)
        row = row*repeat
        yield row
