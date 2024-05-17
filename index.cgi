#! /home/xs254986/miniconda3/bin/python3.8
from wsgiref.handlers import CGIHandler
from html_values import app
CGIHandler().run(app)