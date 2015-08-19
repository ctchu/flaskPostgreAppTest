# -*- coding: utf-8 -*-
"""
Created on Wed Jul 29 21:11:34 2015

@author: Randy
"""

from flask import Flask
flaskApp = Flask(__name__)

import psycopg2
import sys

con = None

try:
        con = psycopg2.connect("dbname='postgres' user='postgres'")    
        
except psycopg2.DatabaseError, e:
        print 'Error %s' % e    
        sys.exit(1)
        
import views