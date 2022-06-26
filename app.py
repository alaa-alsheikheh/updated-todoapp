# Async data requests are requests that get sent to the server and back to the client without a page refresh.
from flask import Flask, jsonify, redirect, render_template, url_for, request, jsonify, abort
from flask_sqlalchemy import SQLAlchemy
import sys
from flask_migrate import Migrate

app=Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI']= 'postgresql://postgres:abc@localhost:5432/todoapp'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db=SQLAlchemy(app)# db obj that links SQLAlchemy to Flask app
# allows use of Flask database migrate commands to initialize, upgrade and downgrade migrations
migrate = Migrate(app, db)# links up Flask app and SQLAlchemy db instance

# models to create and manage to add app functionality?
class Todo(db.Model):# to link to SQLAlchemy, class should inherit from db.model
    __tablename__='todos'
    id=db.Column(db.Integer, primary_key=True)
    description=db.Column(db.String(), nullable=False )
    completed = db.Column(db.Boolean, nullable=False, default=False)
    list_id=db.Column(db.Integer, db.ForeignKey('todolists.id'), nullable=False)
 # to give useful debugging statements when objs are printed,
    # we can define __repr__ to return a to do with the id and desc

    def __repr__(self):
        return f'<Todo ID: {self.id}, description: {self.description}, complete: {self.complete}>'

class TodoList(db.Model):
    __tablename__='todolists'
    id=db.Column(db.Integer, primary_key=True)
    name=db.Column(db.String(), nullable=False)
    todos=db.relationship('Todo',backref='list', lazy=True)

    def __repr__(self) :
        return f'<TodoList ID: {self.id}, name: {self.name}, todos: {self.todos}>'

#db.create_all()  is no longer needed with migrationsd
# sync up models with db using db.create_all
#db.create_all()  # ensures tables are created for all models declared

# create url and url handler on our server, by defining route that listens to todos/create
@app.route('/todos/create', methods=['POST'])
def create_todo():
    body={}
    error=False
    
    try:
        description=request.get_json()['description']
        list_id = request.get_json()['list_id']
        # use description to create new todo obj
        todo=Todo(description=description, completed=False, list_id=list_id)
        db.session.add(todo)
        db.session.commit()
        body['id'] = todo.id
        body['description']=todo.description
        body['completed'] = todo.completed
        
    except:
        error=True
        db.session.rollback()
         # could be useful debugging statement, ->
        print(sys.exc_info())# but terminal may also raise error for you
    finally:
        db.session.close()
        # we'd now tell the controller what to render to the user, by
        # telling the view to re-direct to the index route & re-show the index pg
        if error:
            abort(400)
        else:
            return jsonify(body)#name of route handler that listens for chnage on the index route

@app.route('/todos/<todo_id>/set-completed',methods=['POST'])
def set_completed_todo(todo_id):
    error=False
    try:
        completed= request.get_json()['completed']
        print('completed',completed)
        todo=Todo.query.get(todo_id)
        todo.completed =completed 
        db.session.commit()
    except:
        db.session.rollback()
    finally:
        db.session.close()
        if error:
           abort(400)
        else:
           return jsonify({'success': True})  # command that grabs a fresh list of to do items

@app.route('/todos/<todo_id>/set-complete', methods=['POST'])
def update_todo(todo_id):
    error = False
    try:
        complete = request.get_json()['complete']
        todo = Todo.query.get(todo_id)
        print('Todo: ', todo)
        todo.complete = complete
        db.session.commit()
    except:
        db.session.rollback()
        error = True
        print(sys.exc_info())
    finally:
        db.session.close()
    if error:
        abort(500)
    else:
        return redirect(url_for('index'))

@app.route ('/todos/<todo_id>/delete',methods=['DELETE'])
def delete_todo(todo_id):
    error = False
    try:
        Todo.query.filter_by(id=todo_id).delete()
        db.session.commit()
    except:
        db.session.rollback()
        error = True
    finally:
        db.session.close()
    if error:
        abort(500)
    else:
        return jsonify({ 'success': True })

@app.route('/lists/<list_id>')
def get_list_todos(list_id):
  return render_template('index.html',
  lists=TodoList.query.all(),
  active_list=TodoList.query.get(list_id),
  todos=Todo.query.filter_by(list_id=list_id).order_by('id').all()
  
)

@app.route('/lists/creste', methods=['POST'])
def create_list():
    error=Falsebody={}
    try:
        name=request.get_json()['name']
        todolist=TodoList(name=name)
        db.session.add(todolist)
        db.session.commit()
        body['id']=todolist.id
        body['name']=todolist.name
    except:
        db.session.rollback()
        error = True
        print(sys.exc_info)
    finally:
        db.session.close()
    if error:
        abort(500)
    else:
        return jsonify(body)

@app.route('/lists/<list_id>/delete', methods=['DELETE'])
def delete_list(list_id):
    error = False
    try:
        list = TodoList.query.get(list_id)
        for todo in list.todos:
            db.session.delete(todo)

        db.session.delete(list)
        db.session.commit()
    except:
        db.session.rollback()
        error = True
    finally:
        db.session.close()
    if error:
        abort(500)
    else:
        return jsonify({'success': True})


@app.route('/lists/<list_id>/set-completed', methods=['POST'])
def set_completed_list(list_id):
    error = False

    try:
        list = TodoList.query.get(list_id)

        for todo in list.todos:
            todo.completed = True

        db.session.commit()
    except:
        db.session.rollback()

        error = True
    finally:
        db.session.close()

    if error:
        abort(500)
    else:
        return '', 200
# route to listen to homepage
@app.route('/')
def index():
     # render_template method allows you to specify that an HTML file be rendered to the user
    return redirect(url_for('get_list_todos', list_id=1))  # modifying to replace dummy data with real data

if __name__ == '__main__':
   app.debug = True
   app.run(host="0.0.0.0", port=3000)

   # How does Flask allow you to use data inside of HTML templates?
# By proccessing those HTML templates with Jinja2
#  Jinja allows thatnon-HTML gets embedded inside of HTML files by,
# processing entire file, with the template strings that were in HTML file,
# and then rendering an HTML to the user