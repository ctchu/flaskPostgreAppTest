# -*- coding: utf-8 -*-
"""
Created on Wed Jul 29 21:12:42 2015

@author: Randy
"""

from flask import render_template
from flask import request, redirect
from flask import jsonify
from flask import make_response
from flask import abort
from flask import url_for

from flask.ext.cors import cross_origin

import sys
#import copy
import logging
logging.basicConfig(filename='.\\log\\logfile.log', filemode='w', level=logging.INFO)

from app import flaskApp
from app import con

import psycopg2
import psycopg2.extras
from psycopg2.extensions import AsIs

localTasks = [
    {
        'id': 1,
        'title': u'Buy groceries',
        'description': u'Milk, Cheese, Pizza, Fruit, Tylenol',
        'done': False
    },
    {
        'id': 2,
        'title': u'Learn Python',
        'description': u'Need to find a good Python tutorial on the web',
        'done': False
    }
]

#===========================================
#===========================================
def getTable(category):
    table = []
    
    executeString = "SELECT * FROM {0}".format(category)
    try:
        cur = con.cursor(cursor_factory=psycopg2.extras.DictCursor)    
        cur.execute(executeString)
        
        while True:
          
            row = cur.fetchone()
            
            if row == None:
                break
            
#            for index in row.keys():
#                entry[index] = copy.deepcopy(row[index])
            #entry = json.dumps(row)

            table.append(dict(row))
            #print entry.keys()
    
    except psycopg2.DatabaseError, e:
        print 'Error %s' % e    
        sys.exit(1)
    
    return table

#===========================================
#===========================================
def getTableEntryById(category, targetId):
    
    executeString = "SELECT * FROM {0} WHERE id = {1}".format(category, targetId)
    try:
        cur = con.cursor(cursor_factory=psycopg2.extras.DictCursor)    
        cur.execute(executeString)
        
        row = cur.fetchone()
        if row is not None:            
            return dict(row)
        else:
            return None
        #for index in row.keys():
            #entry[index] = copy.deepcopy(row[index])
             
    except psycopg2.DatabaseError, e:
        print 'Error %s' % e    
        sys.exit(1)
    
#===========================================
#===========================================
def addTableColumn(category, columns, typeString):
    
    executeString = "alter table {0} add column %s {1}".format(category, typeString)
    ## e.g., "alter table Tasks add column %s char(40)"
    ## columns = ['add1', 'add2']
    
    try:
        cur = con.cursor(cursor_factory=psycopg2.extras.DictCursor)    
        cur.execute(executeString)
        
        for c in columns:
            cur.execute(executeString, (AsIs(c),))
    
        con.commit()
             
    except psycopg2.DatabaseError, e:
        print 'Error %s' % e    
        sys.exit(1)

#===========================================
#===========================================
def addTableColumnWithArrayType(category, columns):
    
    typeString = "float[]"
    
    executeString = "alter table {0} add column %s {1}".format(category, typeString)
    
    try:
        cur = con.cursor(cursor_factory=psycopg2.extras.DictCursor)    
        cur.execute(executeString)
        
        for c in columns:
            cur.execute(executeString, (AsIs(c),))
        
        #query = "UPDATE Tasks SET add6 = ARRAY{0} WHERE id = 55".format(table['feature'])
        
        con.commit()
             
    except psycopg2.DatabaseError, e:
        print 'Error %s' % e    
        sys.exit(1)
        
#===========================================
#===========================================
def dropTableColumn(category, columns):
    
    executeString = "alter table {0} drop column %s".format(category)
    ## e.g., "alter table Tasks drop column %s"
    
    try:
        cur = con.cursor(cursor_factory=psycopg2.extras.DictCursor)    
        cur.execute(executeString)
        
        for c in columns:
            cur.execute(executeString, (AsIs(c),))
    
        con.commit()
             
    except psycopg2.DatabaseError, e:
        print 'Error %s' % e    
        sys.exit(1)
        
#===========================================
#===========================================
@flaskApp.route('/')
@flaskApp.route('/index')
def index_page():
    author = "Me"
    name = "Randy"
    return render_template('index.html', author=author, name=name)
    
#===========================================
#===========================================
@flaskApp.route('/signup', methods = ['POST'])
def sign_up():
    email = request.form['email']
    print("The email address is '" + email + "'")
    return redirect('/')
    
#===========================================
#===========================================    
@flaskApp.errorhandler(404) 
def not_found(error):
    return make_response(jsonify({'error': 'Not found'}), 404)

#===========================================
#===========================================    
def make_public_task(task):
    task['uri'] = url_for('get_task', queryId=task['id'], _external=True)
    
#===========================================
#===========================================    
@flaskApp.route('/api/v1.0/tasks', methods=['GET'])
@cross_origin(allow_headers=['Content-Type'])
def get_tasks():
    logging.info("test /api/v1.0/tasks api");

    table = getTable('Tasks')     
    
    map(make_public_task, table)
    
    return jsonify({'tasks': table})
    
#===========================================
#===========================================
@flaskApp.route('/api/v1.0/tasks/<int:queryId>', methods=['GET'])
def get_task(queryId):
    logging.info("test /api/v1.0/tasks/id api");
    
    """task = filter(lambda t: t['id'] == queryId, tasks)
    if len(task) == 0:
        abort(404)"""
    
    selectedTableEntry = getTableEntryById('Tasks', queryId);        
    
    if not selectedTableEntry:
        abort(404)
    
    #both works
    #return jsonify(task=selectedTableEntry)
    return jsonify({'task': selectedTableEntry})

#===========================================
#===========================================    
@flaskApp.route('/api/v1.0/tasks', methods=['POST'])
def create_task():
    if not request.json or not 'title' in request.json or not 'id' in request.json:
        abort(400)
    
    task = {
        'id': request.json['id'],
        'title': request.json['title'],
        'description': request.json.get('description', ""),
        'done': request.json.get('done', "false"),
    }
    
    category = 'Tasks'
    executeString = "SELECT * FROM {0}".format(category)
    try:
        cur = con.cursor(cursor_factory=psycopg2.extras.DictCursor)    
        cur.execute(executeString)
#        table = cur.fetchall()
#        if len(table) == 0:
#            abort(400)

        #method 1:        
        keyString = ",".join(['"%s"' % k for k in task])    # "description","done","id","title"
        valueString = ",".join(["%s",] * len(task.keys()))    # %s,%s,%s,%s
        
        query = "insert into Tasks (%s) values (%s)" % (keyString, valueString)
        
        cur.execute(query, tuple(task.values()))
        
        #method 2:
        #cur.execute("insert into Tasks VALUES(16, 'test', 'testt', 'test2')")        
        
        #method 3:        
        #s = "insert into Tasks VALUES({0},'{1}','{2}','{3}')".format(task['id'], task['title'], task['description'], task['done'])       
        #cur.execute(s)
        
        con.commit()
    
    except psycopg2.DatabaseError, e:
        print 'Error %s' % e    
        sys.exit(1)
    
    return jsonify({'task': task}), 201
## Correct curl cmd in windows: curl -i -H "Content-Type: application/json" -X POST -d "{""title"":""Test Succeed"", ""id"":""101""}" http://localhost:5000/api/v1.0/tasks

#===========================================
#===========================================
@flaskApp.route('/api/v1.0/tasks', methods=['PUT'])
def update_task():
    if not request.json or not 'id' in request.json:
        abort(400)
    
    category = 'Tasks'
    updateId = request.json['id']
    task = getTableEntryById(category, updateId)
    if not task:
        abort(404)
    
    try:
        cur = con.cursor(cursor_factory=psycopg2.extras.DictCursor)   
        executePushStrings = []
        for keyInTarget in task.keys():
            if keyInTarget == 'id':
                continue
            
            requestValue = request.json.get(keyInTarget, "")

            if requestValue is not "":     
                if isinstance(requestValue, basestring):
                    executePushString = "UPDATE {0} SET {1} = '{2}' WHERE id = {3}".format(category, keyInTarget, requestValue, updateId)
                    print 'requestValue is string'
                else:
                    executePushString = "UPDATE {0} SET {1} = {2} WHERE id = {3}".format(category, keyInTarget, requestValue, updateId)
                    print 'requestValue is not string'
                
                executePushStrings.append(executePushString)
                #cur.execute("UPDATE Tasks SET done = true WHERE id = 15")
                
        for executePushString in executePushStrings:
            cur.execute(executePushString)
            con.commit()
            
    except psycopg2.DatabaseError, e:
        print 'Error %s' % e    
        sys.exit(1)
        
    return jsonify({'result': True})
    
    
#    if len(task) == 0:
#        abort(404)
#    if not request.json:
#        abort(400)
#    if 'title' in request.json and type(request.json['title']) != unicode:
#        abort(400)
#    if 'description' in request.json and type(request.json['description']) is not unicode:
#        abort(400)
#    if 'done' in request.json and type(request.json['done']) is not bool:
#        abort(400)
#    task[0]['title'] = request.json.get('title', task[0]['title'])
#    task[0]['description'] = request.json.get('description', task[0]['description'])
#    task[0]['done'] = request.json.get('done', task[0]['done'])
#    return jsonify({'task': task[0]})
### Correct curl command in windowsL : curl -i -H "Content-Type: application/json" -X PUT -d "{""id"":100, ""done"":""true""}" http://localhost:5000/api/v1.0/tasks
    
#===========================================
#===========================================
@flaskApp.route('/api/v1.0/tasks/<int:task_id>', methods=['DELETE'])
def delete_task(task_id):
        
    category = 'Tasks'
    executeSearchString = "SELECT FROM {0} WHERE id = {1}".format(category, task_id)
    executeDeleteString = "DELETE FROM {0} WHERE id = {1} ".format(category, task_id)
    try:
        cur = con.cursor(cursor_factory=psycopg2.extras.DictCursor)    
        cur.execute(executeSearchString)
        
        row = cur.fetchone()
        if row is None:
            abort(400)
        
        cur.execute(executeDeleteString)
        
        con.commit()
    
    except psycopg2.DatabaseError, e:
        print 'Error %s' % e    
        sys.exit(1)
        
    return jsonify({'result': True})
### Correct curl command in windowsL : curl -i -H "Content-Type: application/json" -X DELETE http://localhost:5000/api/v1.0/tasks/15
