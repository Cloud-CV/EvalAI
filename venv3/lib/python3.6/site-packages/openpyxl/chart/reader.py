from __future__ import absolute_import
# Copyright (c) 2010-2018 openpyxl

"""
Read a chart
"""

from .chartspace import ChartSpace, PlotArea
from openpyxl.xml.functions import fromstring

from openpyxl.packaging.relationship import get_rel, get_rels_path, get_dependents
from openpyxl.drawing.spreadsheet_drawing import SpreadsheetDrawing

_types = ('areaChart', 'area3DChart', 'lineChart', 'line3DChart',
         'stockChart', 'radarChart', 'scatterChart', 'pieChart', 'pie3DChart',
         'doughnutChart', 'barChart', 'bar3DChart', 'ofPieChart', 'surfaceChart',
         'surface3DChart', 'bubbleChart',)

_axes = ('valAx', 'catAx', 'dateAx', 'serAx',)


def read_chart(chartspace):
    cs = chartspace
    plot = cs.chart.plotArea

    chart = plot._charts[0]
    chart._charts = plot._charts

    chart.title = cs.chart.title
    chart.layout = plot.layout
    chart.legend = cs.chart.legend

    # 3d attributes
    chart.floor = cs.chart.floor
    chart.sideWall = cs.chart.sideWall
    chart.backWall = cs.chart.backWall

    return chart


def find_charts(archive, path):
    """
    Given the path to a drawing file extract anchors with charts
    """

    src = archive.read(path)
    tree = fromstring(src)
    drawing = SpreadsheetDrawing.from_tree(tree)

    rels_path = get_rels_path(path)
    deps = []
    if rels_path in archive.namelist():
        deps = get_dependents(archive, rels_path)

    charts = []
    for rel in drawing._chart_rels:
        cs = get_rel(archive, deps, rel.id, ChartSpace)
        chart = read_chart(cs)
        chart.anchor = rel.anchor
        charts.append(chart)

    return charts
