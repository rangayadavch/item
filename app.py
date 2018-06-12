from flask import Flask, render_template
from flask import url_for, request
from flask import redirect, flash
from flask import jsonify, make_response
from functools import wraps
from flask import session as login_session
import random
import string
from sqlalchemy import create_engine, asc, desc
from sqlalchemy.orm import sessionmaker
from database_setup import *
from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError
import os
import datetime
import json
import httplib2
import requests
# Import login_required from login_decorator.py
from login_decorator import login_required


app = Flask(__name__)


CLIENT_ID = json.loads(open('client_secrets.json', 'r').read())['web']['client_id']
APPLICATION_NAME = "Item-Catalog-Project"


# Connect to database
engine = create_engine('sqlite:///itemcatalog.db')
Base.metadata.bind = engine
# Create session
DBSession = sessionmaker(bind=engine)
session = DBSession()

def login_required(f):
    '''Checks to see whether a user is logged in'''
    @wraps(f)
    def y(*args, **kwargs):
        if 'username' not in login_session:
            return redirect('/login')
        return f(*args, **kwargs)
    return y

@app.route('/catalog/JSON')
def allItemsJSON():
    categories = session.query(Type).all()
    type_dict = [c.serialize for c in categories]
    for c in range(len(type_dict)):
        items = [i.serialize for i in session.query(Items)\
                    .filter_by(type_id=type_dict[c]["id"]).all()]
        if items:
            type_dict[c]["Item"] = items
    return jsonify(Type=type_dict)

@app.route('/catalog/categories/JSON')
def categoriesJSON():
    categories = session.query(Type).all()
    return jsonify(categories=[c.serialize for c in categories])

@app.route('/catalog/items/JSON')
def itemsJSON():
    items = session.query(Items).all()
    return jsonify(items=[i.serialize for i in items])

@app.route('/catalog/<path:type_name>/items/JSON')
def typeItemsJSON(type_name):
    type = session.query(Type).filter_by(name=type_name).one()
    items = session.query(Items).filter_by(type=type).all()
    return jsonify(items=[i.serialize for i in items])

@app.route('/catalog/<path:type_name>/<path:item_name>/JSON')
def ItemJSON(type_name, item_name):
    type = session.query(Type).filter_by(name=type_name).one()
    item = session.query(Items).filter_by(name=item_name,\
                                        type=type).one()
    return jsonify(item=[item.serialize])

# Homepage
@app.route('/')
@app.route('/catalog/')
def showType():
    categories = session.query(Type).order_by(asc(Type.name))
    items = session.query(Items).order_by(desc(Items.date)).limit(5)
    return render_template('catalog.html',
                            categories = categories,
                            items = items)

# Type of Items
@app.route('/catalog/<path:type_name>/items/')
def showType(type_name):
    categories = session.query(Type).order_by(asc(Type.name))
    type = session.query(Type).filter_by(name=type_name).one()
    items = session.query(Items).filter_by(type=type).order_by(asc(Items.name)).all()
    print items
    count = session.query(Items).filter_by(type=type).count()
    creator = getUserInfo(type.user_id)
    if 'username' not in login_session or creator.id != login_session['user_id']:
        return render_template('public_items.html',
                                type = type.name,
                                categories = categories,
                                items = items,
                                count = count)
    else:
        user = getUserInfo(login_session['user_id'])
        return render_template('items.html',
                                type =type.name,
                                categories = categories,
                                items = items,
                                count = count,
                                user=user)

# Add a type
@app.route('/catalog/addtype', methods=['GET', 'POST'])
@login_required
def addType():
    if request.method == 'POST':
        newType = Type(
            name=request.form['name'],
            user_id=login_session['user_id'])
        print newType
        session.add(newType)
        session.commit()
        flash('Type Successfully Added!')
        return redirect(url_for('showType'))
    else:
        return render_template('addtype.html')

# Display a Specific Item
@app.route('/catalog/<path:type_name>/<path:item_name>/')
def showItem(type_name, item_name):
    item = session.query(Items).filter_by(name=item_name).one()
    creator = getUserInfo(item.user_id)
    categories = session.query(Type).order_by(asc(Type.name))
    if 'username' not in login_session or creator.id != login_session['user_id']:
        return render_template('public_itemdetail.html',
                                item = item,
                                type = type_name,
                                categories = categories,
                                creator = creator)
    else:
        return render_template('itemdetail.html',
                                item = item,
                                type = type_name,
                                categories = categories,
                                creator = creator)


@app.route('/catalog/add', methods=['GET', 'POST'])
@login_required
def addItem():
    categories = session.query(Type).all()
    if request.method == 'POST':
        newItem = Items(
            name=request.form['name'],
            description=request.form['description'],
            picture=request.form['picture'],
            type=session.query(Type).filter_by(name=request.form['type']).one(),
            date=datetime.datetime.now(),
            user_id=login_session['user_id'])
        session.add(newItem)
        session.commit()
        flash('Item Successfully Added!')
        return redirect(url_for('showType'))
    else:
        return render_template('additem.html',
                                categories=categories)

# Edit a type
@app.route('/catalog/<path:type_name>/edit', methods=['GET', 'POST'])
@login_required
def editType(type_name):
    editedType = session.query(Type).filter_by(name=type_name).one()
    type = session.query(Type).filter_by(name=type_name).one()
    # See if the logged in user is the owner of item
    creator = getUserInfo(editedType.user_id)
    user = getUserInfo(login_session['user_id'])
    # If logged in user != item owner redirect them
    if creator.id != login_session['user_id']:
        flash ("You cannot edit this Type. This Type belongs to %s" % creator.name)
        return redirect(url_for('showType'))
    # POST methods
    if request.method == 'POST':
        if request.form['name']:
            editedType.name = request.form['name']
        session.add(editedType)
        session.commit()
        flash('Type Item Successfully Edited!')
        return  redirect(url_for('showType'))
    else:
        return render_template('edittype.html',
                                categories=editedType,
                                type = type)

# Edit an item
@app.route('/catalog/<path:type_name>/<path:item_name>/edit', methods=['GET', 'POST'])
@login_required
def editItem(type_name, item_name):
    editedItem = session.query(Items).filter_by(name=item_name).one()
    categories = session.query(Type)
    # See if the logged in user is the owner of item
    creator = getUserInfo(editedItem.user_id)
    user = getUserInfo(login_session['user_id'])
    # If logged in user != item owner redirect them
    if creator.id != login_session['user_id']:
        flash ("You cannot edit this item. This item belongs to %s" % creator.name)
        return redirect(url_for('showCatalog'))
    # POST methods
    if request.method == 'POST':
        if request.form['name']:
            editedItem.name = request.form['name']
        if request.form['description']:
            editedItem.description = request.form['description']
        if request.form['picture']:
            editedItem.picture = request.form['picture']
        if request.form['type']:
            type = session.query(Type).filter_by(name=request.form['type']).one()
            editedItem.type = type
        time = datetime.datetime.now()
        editedItem.date = time
        session.add(editedItem)
        session.commit()
        flash('Type Item Successfully Edited!')
        return  redirect(url_for('showType',
                                type_name=editedItem.type.name))
    else:
        return render_template('edititem.html',
                                item=editedItem,
                                categories=categories)
# Delete a type
@app.route('/catalog/<path:type_name>/delete', methods=['GET', 'POST'])
@login_required
def deleteType(type_name):
    typeToDelete = session.query(Type).filter_by(name=type_name).one()
    # See if the logged in user is the owner of item
    creator = getUserInfo(typeToDelete.user_id)
    user = getUserInfo(login_session['user_id'])
    # If logged in user != item owner redirect them
    if creator.id != login_session['user_id']:
        flash ("You cannot delete this Type. This Type belongs to %s" % creator.name)
        return redirect(url_for('showType'))
    if request.method =='POST':
        session.delete(typeToDelete)
        session.commit()
        flash('Type Successfully Deleted! '+typeToDelete.name)
        return redirect(url_for('showType'))
    else:
        return render_template('deletetype.html',
                                type=typeToDelete)



# Delete an item
@app.route('/catalog/<path:type_name>/<path:item_name>/delete', methods=['GET', 'POST'])
@login_required
def deleteItem(type_name, item_name):
    itemToDelete = session.query(Items).filter_by(name=item_name).one()
    type = session.query(Type).filter_by(name=type_name).one()
    categories = session.query(Type).all()
    # See if the logged in user is the owner of item
    creator = getUserInfo(itemToDelete.user_id)
    user = getUserInfo(login_session['user_id'])
    # If logged in user != item owner redirect them
    if creator.id != login_session['user_id']:
        flash ("You cannot delete this item. This item belongs to %s" % creator.name)
        return redirect(url_for('showType'))
    if request.method =='POST':
        session.delete(itemToDelete)
        session.commit()
        flash('Item Successfully Deleted! '+itemToDelete.name)
        return redirect(url_for('showType',
                                type_name=type.name))
    else:
        return render_template('deleteitem.html',
                                item=itemToDelete)






# Login session
@app.route('/login')
def showLogin():
    state = ''.join(
        random.choice(string.ascii_uppercase + string.digits) for y in range(32))
    login_session['state'] = state
    # return "The current session state is %s" % login_session['state']
    return render_template('login.html', STATE=state)

# GConnect
@app.route('/gconnect', methods=['POST'])
def gconnect():
    # Validate state token
    if request.args.get('state') != login_session['state']:
        response = make_response(json.dumps('Invalid state parameter.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    # Obtain authorization code, now compatible with Python3
    request.get_data()
    code = request.data.decode('utf-8')

    try:
        # Upgrade the authorization code into a credentials object
        oauth_flow = flow_from_clientsecrets('client_secrets.json', scope='')
        oauth_flow.redirect_uri = 'postmessage'
        credentials = oauth_flow.step2_exchange(code)
    except FlowExchangeError:
        response = make_response(
            json.dumps('Failed to upgrade the given the code.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Check that the access token is valid.
    access_token = credentials.access_token
    url = ('https://www.googleapis.com/oauth2/v1/tokeninfo?access_token=%s'
           % access_token)
    # Submit request, parse response - Python3 compatible
    h = httplib2.Http()
    response = h.request(url, 'GET')[1]
    str_response = response.decode('utf-8')
    result = json.loads(str_response)

    # If there was an error in the access token info, abort.
    if result.get('error') is not None:
        response = make_response(json.dumps(result.get('error')), 500)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is used for the intended user.
    gplus_id = credentials.id_token['sub']
    if result['user_id'] != gplus_id:
        response = make_response(
            json.dumps("Token's user ID is not match given user ID."), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is valid for this app.
    if result['issued_to'] != CLIENT_ID:
        response = make_response(
            json.dumps("Token's client ID does not match app's."), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    stored_access_token = login_session.get('access_token')
    stored_gplus_id = login_session.get('gplus_id')
    if stored_access_token is not None and gplus_id == stored_gplus_id:
        response = make_response(json.dumps('Current user is already connected.'),
                                 200)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Store the access token in the session for later use.
    login_session['access_token'] = access_token
    login_session['gplus_id'] = gplus_id

    # Get user info
    userinfo_url = "https://www.googleapis.com/oauth2/v1/userinfo"
    params = {'access_token': access_token, 'alt': 'json'}
    answer = requests.get(userinfo_url, params=params)

    data = answer.json()

    login_session['username'] = data['name']
    login_session['picture'] = data['picture']
    login_session['email'] = data['email']

    # see if user exists, if it doesn't make a new one
    user_id = getUserID(login_session['email'])
    if not user_id:
        user_id = createUser(login_session)
    login_session['user_id'] = user_id

    output = ''
    output += '<h1>Welcome,Ranga '
    output += login_session['username']
    output += '!</h1>'
    output += '<img src="'
    output += login_session['picture']
    output += ' " style = "width: 300px; height: 300px;border-radius: 150px;-webkit-border-radius: 150px;-moz-border-radius: 150px;"> '
    flash("you are now logged in as %s" % login_session['username'])
    return output

# User Helper Functions


def createUser(login_session):
    newUser = User(name=login_session['username'], email=login_session[
                   'email'], picture=login_session['picture'])
    session.add(newUser)
    session.commit()
    user = session.query(User).filter_by(email=login_session['email']).one()
    return user.id


def getUserInfo(user_id):
    user = session.query(User).filter_by(id=user_id).one()
    return user


def getUserID(email):
    try:
        user = session.query(User).filter_by(email=email).one()
        return user.id
    except:
        return None

# DISCONNECT - Revoke a current user's token and reset their login_session


@app.route('/gdisconnect')
def gdisconnect():
        # Only disconnect a connected user.
    access_token = login_session.get('access_token')
    if access_token is None:
        response = make_response(
            json.dumps('Current user not connected.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    url = 'https://accounts.google.com/o/oauth2/revoke?token=%s' % access_token
    h = httplib2.Http()
    result = h.request(url, 'GET')[0]
    if result['status'] == '200':
        # Reset the user's sesson.
        del login_session['access_token']
        del login_session['gplus_id']
        del login_session['username']
        del login_session['email']
        del login_session['picture']

        # response = make_response(json.dumps('Successfully disconnected.'), 200)
        # response.headers['Content-Type'] = 'application/json'
        response = redirect(url_for('showType'))
        flash("You are now logged out.")
        return response
    else:
        # For whatever reason, the given token was invalid.
        response = make_response(
            json.dumps('Failed to revoke token for given user.', 400))
        response.headers['Content-Type'] = 'application/json'
        return response

# remove when deployed
@app.context_processor
def override_url_for():
    return dict(url_for=dated_url_for)

def dated_url_for(endpoint, **values):
    if endpoint == 'static':
        filename = values.get('filename', None)
        if filename:
            file_path = os.path.join(app.root_path,
                                     endpoint, filename)
            values['q'] = int(os.stat(file_path).st_mtime)
    return url_for(endpoint, **values)


if __name__ == '__main__':
    app.debug = True
    app.secret_key = 'super_secret_key'
    app.run(host = '0.0.0.0', port = 5000)
