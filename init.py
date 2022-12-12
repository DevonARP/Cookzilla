from flask import Flask, render_template, request, session, url_for, redirect, flash
import pymysql.cursors
from werkzeug.utils import secure_filename
import cloudinary
import cloudinary.uploader
import cloudinary.api
import bcrypt
salt = bcrypt.gensalt()

cloudinary.config(
cloud_name = "drrr3ca5o",
api_key = "265839145787376",
api_secret = "CRbhBA4xu-J0htxccVAEPeDtZkg"
)

app = Flask(__name__)

conn = pymysql.connect(host='localhost',
                       port = 3306,
                       user='root',
                       password='root',
                       db='project',
                       charset='utf8mb4',
                       cursorclass=pymysql.cursors.DictCursor)



#Define a route to login or register page
@app.route('/')
def index():
    return render_template('index.html')

#Define route for login
@app.route('/login')
def login():
    return render_template('login.html')

#Define route for register
@app.route('/register')
def register():
    return render_template('register.html')

#Authenticates the login
@app.route('/loginAuth', methods=['GET', 'POST'])
def loginAuth():
    username = request.form['username']
    password = request.form['password']
    hashed = bcrypt.hashpw(password.encode('utf8'), salt)
    cursor = conn.cursor()
    query = 'SELECT * FROM person WHERE username = %s and password = %s'
    cursor.execute(query, (username, hashed))
    data = cursor.fetchone()
    cursor.close()
    error = None
    if(data):
        session['username'] = username
        return redirect(url_for('home'))
    else:
        error = 'Invalid login or username'
        return render_template('login.html', error=error)

#Authenticates the register
@app.route('/registerAuth', methods=['GET', 'POST'])
def registerAuth():
    username = request.form['username']
    password = request.form['password']
    hashed = bcrypt.hashpw(password.encode('utf8'), salt)
    fname = request.form['fname']
    lname = request.form['lname']
    email = request.form['email']
    profile = request.form['profile']
    cursor = conn.cursor()
    query = 'SELECT * FROM person WHERE username = %s'
    cursor.execute(query, (username))
    data = cursor.fetchone()
    error = None
    if(data):
        error = "This user already exists"
        return render_template('register.html', error = error)
    else:
        ins = 'INSERT INTO person VALUES(%s, %s, %s, %s, %s, %s)'
        cursor.execute(ins, (username, hashed, fname, lname, email, profile))
        conn.commit()
        cursor.close()
        return render_template('index.html')

#home page
@app.route('/home')
def home():
    username = session['username']
    cursor = conn.cursor();
    query = 'SELECT title FROM recipe WHERE postedBy = %s ORDER BY title'
    cursor.execute(query, (username))
    data = cursor.fetchall()
    cursor.close()
    cursor = conn.cursor();
    query = 'SELECT gName FROM groupmembership WHERE memberName = %s ORDER BY gName'
    cursor.execute(query, (username))
    data2 = cursor.fetchall()
    query = 'SELECT * FROM event INNER JOIN groupmembership ON event.gName = groupmembership.gName WHERE groupmembership.memberName = %s AND event.eDate >= CURRENT_TIMESTAMP() ORDER BY event.eDate'
    cursor.execute(query, (username))
    data3 = cursor.fetchall()
    query = 'SELECT * FROM event INNER JOIN rsvp ON event.eID = rsvp.eID WHERE rsvp.response = 1 AND event.eDate >= CURRENT_TIMESTAMP() AND rsvp.userName = %s ORDER BY event.eDate'
    cursor.execute(query, (username))
    data4 = cursor.fetchall()
    query = 'SELECT * FROM review WHERE userName = %s ORDER BY revTitle'
    cursor.execute(query, (username))
    data5 = cursor.fetchall()
    return render_template('home.html', username=username, rposts=data, gposts=data2, edata=data3, redata=data4, viewdata=data5)

#search 
@app.route('/search', methods=['GET', 'POST'])
def search():
    username = session['username']
    return render_template('search.html', username=username)


@app.route('/searching', methods=['GET', 'POST'])
def searching():
    username = session['username']
    cursor = conn.cursor();
    filter = request.form['filter']
    filter = "%" + filter +"%"
    query = 'SELECT DISTINCT recipe.title, recipe.recipeID, recipe.postedBy FROM recipe LEFT JOIN recipetag ON recipe.recipeID = recipetag.recipeID WHERE recipetag.tagText LIKE %s OR recipe.recipeID LIKE %s OR recipe.postedBy LIKE %s OR recipe.title LIKE %s'
    cursor.execute(query, (filter, filter, filter, filter))
    data = cursor.fetchall()
    conn.commit()
    cursor.close()
    if(data):
        return render_template('results.html', username=username, info=data)
    else:
        error="No results found"
        return render_template('search.html', error=error)

#group page
@app.route('/group', methods=['GET', 'POST'])
def group():
    username = session['username']
    return render_template('group.html', username=username)

#create a group page
@app.route('/create', methods=['GET', 'POST'])
def create():
    username = session['username']
    return render_template('create.html', username=username)

#creating group
@app.route('/creating', methods=['GET', 'POST'])
def creating():
    username = session['username']
    gname = request.form['gname']
    gdesc = request.form['gdesc']
    cursor = conn.cursor()
    query = 'SELECT * FROM `group` WHERE gName = %s AND gCreator = %s'
    cursor.execute(query, (gname, username))
    data = cursor.fetchone()
    error = None
    if(data):
        error = "You already have a group with this name"
        return render_template('create.html', error = error, username=username)
    else:
        ins = 'INSERT INTO `group` VALUES(%s, %s, %s)'
        cursor.execute(ins, (gname, username, gdesc))
        conn.commit()
        ins = 'INSERT INTO groupmembership VALUES(%s, %s, %s)'
        cursor.execute(ins, (username, gname, username))
        conn.commit()
        cursor.close()
        return redirect(url_for('home'))

#join a group page
@app.route('/join', methods=['GET', 'POST'])
def join():
    username = session['username']
    cursor = conn.cursor();
    query = 'SELECT * from `group` INNER JOIN groupmembership ON `group`.gName = groupmembership.gName AND `group`.gCreator = groupmembership.gCreator WHERE groupmembership.memberName != %s'
    cursor.execute(query, (username))
    data = cursor.fetchall()
    cursor.close()
    error=None
    if(data):
        return render_template('join.html', gdata=data, username=username)
    else:
        error = "There are no groups to choose from."
        return render_template('group.html', error = error)
#joining group
@app.route('/join_group', methods=['GET', 'POST'])
def join_group():
    username = session['username']
    joingroup = request.args['joingroup']
    cursor = conn.cursor()
    l1=list(joingroup.split(","))
    gname = l1[0]
    gcreator = l1[1]
    query = 'SELECT * FROM groupmembership WHERE gCreator = %s AND gName = %s AND memberName = %s'
    cursor.execute(query, (gcreator,gname, username))
    data = cursor.fetchall()
    error=None
    if(data):
        error = "You're already in that group"
        return render_template('group.html', error = error)
    else:
        ins = 'INSERT INTO groupmembership VALUES(%s, %s, %s)'
        cursor.execute(ins, (username, gname, gcreator))
        conn.commit()
        cursor.close()
        return redirect(url_for('home'))

#post page
@app.route('/post', methods=['GET', 'POST'])
def post():
    username = session['username']
    return render_template('post.html', username=username)

#ingredient page
@app.route('/ingredient', methods=['GET', 'POST'])
def ingredient():
    username = session['username']
    return render_template('ingredient.html', username=username)

#Submit ingredient
@app.route('/ingredientAuth', methods=['GET', 'POST'])
def ingredientAuth():
    username = session['username']
    name = request.form['name']
    link = request.form['link']
    cursor = conn.cursor()
    query = 'SELECT * FROM ingredient WHERE iName = %s'
    cursor.execute(query, (name))
    data = cursor.fetchone()
    error = None
    if(data):
        error = "This ingredient name already exists"
        return render_template('ingredient.html', error = error)
    else:
        ins = 'INSERT INTO ingredient VALUES(%s, %s)'
        cursor.execute(ins, (name, link))
        conn.commit()
        cursor.close()
        return redirect(url_for('home'))

#recipe page
@app.route('/recipe', methods=['GET', 'POST'])
def recipe():
    username = session['username']
    return render_template('recipe.html', username=username)

#Submit recipe
@app.route('/recipeAuth', methods=['GET', 'POST'])
def recipeAuth():
    username = session['username']
    name = request.form['name']
    servings = request.form['servings']
    cursor = conn.cursor()
    query = 'SELECT MAX(recipeID) FROM recipe'
    cursor.execute(query)
    data = cursor.fetchone()
    data = data.get('MAX(recipeID)')
    if(servings.isnumeric()):
        if(data):
            data = data +1
        else:
            data = 1
        ins = 'INSERT INTO recipe VALUES(%s, %s, %s, %s)'
        cursor.execute(ins, (data, name, servings, username))
        conn.commit()
        cursor.close()
        return redirect(url_for('home'))
    else:
        error = "The serving amount isn't a number"
        return render_template('recipe.html', error = error)

#step page
@app.route('/step', methods=['GET', 'POST'])
def step():
    username = session['username']
    cursor = conn.cursor();
    query = 'SELECT * FROM recipe Where postedBy = %s'
    cursor.execute(query, (username))
    data = cursor.fetchall()
    if(data):
        cursor.close()
        return render_template('step.html', sdata=data, username=username)
    else:
        error = "You have no recipe's to choose from."
        return render_template('post.html', error = error)      

#adding a step page
@app.route('/add_step', methods=['GET', 'POST'])
def add_step():
    username = session['username']
    recipe = request.args['recipe']
    step = request.args['stepnumber']
    sdesc = request.args['sdesc']
    cursor = conn.cursor()
    query = 'SELECT * FROM step WHERE recipeID = %s AND stepNo = %s'
    cursor.execute(query, (recipe, step))
    data= cursor.fetchall()
    error = None
    if(step.isnumeric()):
        if(data):
            error = "You already have that step number for that dish"
            return render_template('post.html', error = error)
        else:
            ins = 'INSERT INTO step VALUES(%s, %s, %s)'
            cursor.execute(ins, (step, recipe, sdesc))
            conn.commit()
            cursor.close()
            return redirect(url_for('home'))
    else:
            error = "The step number isn't a number"
            return render_template('post.html', error = error)

#ingredient to recipe page
@app.route('/recipeingredients', methods=['GET', 'POST'])
def recipeingredients():
    username = session['username']
    cursor = conn.cursor();
    query = 'SELECT * FROM recipe Where postedBy = %s'
    cursor.execute(query, (username))
    data = cursor.fetchall()
    if(data):
        query = 'SELECT iName FROM ingredient'
        cursor.execute(query)
        data2 = cursor.fetchall()
        cursor.close()
        if(data2):
            return render_template('recipeingredients.html', redata=data, idata=data2, username=username)
        else:
            error = "No ingredient to choose from"
            return render_template('post.html', error=error)
    else:
        error = "You have no recipe's to choose from"
        return render_template('post.html', error=error)

#adding an ingredient to recipe page
@app.route('/add_ingred', methods=['GET', 'POST'])
def add_ingred():
    username = session['username']
    recipe = request.args['recipe']
    print(recipe)
    ingred = request.args['ingred']
    amount = request.args['amount']
    unit = request.args['unit']
    cursor = conn.cursor()
    query = 'SELECT * FROM recipeingredient WHERE recipeID = %s AND iName = %s'
    cursor.execute(query, (recipe, ingred))
    data2 = cursor.fetchall()
    error = None
    if(amount.isnumeric()):
        if(data2):
            error = "You already have an amount of that ingredient for that recipe."
            return render_template('post.html', error = error)
        else:
            ins = 'INSERT INTO recipeingredient VALUES(%s, %s, %s, %s)'
            cursor.execute(ins, (recipe, ingred, unit, amount))
            conn.commit()
            cursor.close()
            return redirect(url_for('home'))
    else:
        error = "The amount of the ingredient isn't a number"
        return render_template('post.html', error = error)     

#display page
@app.route('/display', methods=['GET', 'POST'])
def display():
    username = session['username']
    recipe = request.args['id']
    cursor = conn.cursor()
    query = 'SELECT * FROM recipe WHERE recipeID = %s'
    cursor.execute(query, (recipe))
    recipedata = cursor.fetchall()
    query = 'SELECT * FROM recipeingredient INNER JOIN ingredient on recipeingredient.iName = ingredient.iName WHERE recipeID = %s ORDER BY recipeingredient.iName'
    cursor.execute(query, (recipe))
    recipeingreddata = cursor.fetchall()
    query = 'SELECT * FROM recipetag WHERE recipeID = %s'
    cursor.execute(query, (recipe))
    recipetagdata = cursor.fetchall()
    query = 'SELECT * FROM step WHERE recipeID = %s ORDER BY stepNo ASC'
    cursor.execute(query, (recipe))
    stepdata = cursor.fetchall()
    query = 'SELECT * FROM recipepicture WHERE recipeID = %s'
    cursor.execute(query, (recipe))
    imagedata = cursor.fetchall()
    query = 'SELECT * FROM review LEFT JOIN reviewpicture ON review.recipeID = reviewpicture.recipeID AND review.userName = reviewpicture.userName WHERE review.recipeID = %s AND review.userName = %s'
    cursor.execute(query, (recipe, username))
    reviewdata = cursor.fetchall()
    query = 'SELECT AVG(stars) FROM review WHERE recipeID = %s'
    cursor.execute(query, (recipe))
    avgdata = cursor.fetchall()
    avgdata = avgdata[0]['AVG(stars)']
    query = 'SELECT DISTINCT restrictionDesc FROM restrictions INNER JOIN recipeingredient ON restrictions.iName=recipeingredient.iName WHERE recipeID = %s'
    cursor.execute(query, (recipe))
    resdata = cursor.fetchall()
    query = 'SELECT * FROM recipe INNER JOIN relatedrecipe ON recipe.recipeID=relatedrecipe.recipe2 WHERE relatedrecipe.recipe1 = %s'
    cursor.execute(query, (recipe))
    reldata = cursor.fetchall()
    return render_template('display.html', recdata=recipedata, indata=recipeingreddata, tdata=recipetagdata, stdata = stepdata, imdata = imagedata, username=username, revdata = reviewdata, avgdata=avgdata,resdata=resdata,reldata=reldata)

#tags to recipe page
@app.route('/recipetags', methods=['GET', 'POST'])
def recipetags():
    username = session['username']
    cursor = conn.cursor();
    query = 'SELECT * FROM recipe Where postedBy = %s'
    cursor.execute(query, (username))
    data = cursor.fetchall()
    if(data):
        cursor.close()
        return render_template('recipetags.html', redata=data, username=username)
    else:
        error = "You have no recipe's to choose from."
        return render_template('post.html', error = error)       
  
@app.route('/add_tag', methods=['GET', 'POST'])
def add_tag():
    username = session['username']
    recipe = request.args['recipe']
    tag = request.args['tag']
    cursor = conn.cursor()
    query = 'SELECT * FROM recipetag WHERE recipeID = %s AND tagText = %s'
    cursor.execute(query, (recipe, tag))
    data = cursor.fetchall()
    error = None
    if(data):
        error = "You already have this tag for that recipe."
        return render_template('post.html', error = error)
    else:
        ins = 'INSERT INTO recipetag VALUES(%s, %s)'
        cursor.execute(ins, (recipe, tag))
        conn.commit()
        cursor.close()
        return redirect(url_for('home'))

@app.route('/event', methods=['GET', 'POST'])
def event():
    username = session['username']
    cursor = conn.cursor();
    query = 'SELECT DISTINCT gName FROM groupmembership Where gCreator = %s'
    cursor.execute(query, (username))
    data = cursor.fetchall()
    cursor.close()
    if(data):
        return render_template('event.html', edata=data, username=username)
    else:
        error="You have created no groups and therefore can't add an event."
        return render_template('group.html', error=error)

@app.route('/create_event', methods=['GET', 'POST'])
def create_event():
    username = session['username']
    group = request.args['group']
    name = request.args['name']
    desc = request.args['desc']
    date = request.args['date']
    cursor = conn.cursor()
    query = 'SELECT * FROM event WHERE gName = %s AND gCreator = %s AND eDate = %s'
    cursor.execute(query, (group, username, date))
    data = cursor.fetchall()
    error = None
    if(data):
        error = "You already have an event on that date for this group."
        return render_template('group.html', error = error)
    else:
        query = 'SELECT MAX(eID) FROM event'
        cursor.execute(query)
        iddata = cursor.fetchone()
        iddata = iddata.get('MAX(eID)')
        if(iddata):
            iddata = iddata +1
        else:
            iddata = 1
        ins = 'INSERT INTO event VALUES(%s, %s, %s, %s, %s, %s)'
        cursor.execute(ins, (iddata, name, desc, date, group, username))
        conn.commit()
        cursor.close()
        return redirect(url_for('home'))

#ingredient to recipe page
@app.route('/rsvp', methods=['GET', 'POST'])
def rsvp():
    username = session['username']
    cursor = conn.cursor();
    query = 'SELECT * FROM event INNER JOIN groupmembership ON event.gName = groupmembership.gName WHERE groupmembership.memberName = %s AND event.eDate >= CURRENT_TIMESTAMP()'
    cursor.execute(query, (username))
    data = cursor.fetchall()
    cursor.close()
    if(data):
        return render_template('rsvp.html', rdata=data, username=username)
    else:
        error="You have no events coming up for the groups you are apart of."
        return render_template('group.html', error=error)

#adding an ingredient to recipe page
@app.route('/add_rsvp', methods=['GET', 'POST'])
def add_rsvp():
    username = session['username']
    rsvp = request.args['rsvp']
    id = request.args['id']
    cursor = conn.cursor()
    query = 'SELECT * FROM rsvp WHERE rsvp.userName = %s AND rsvp.eID = %s'
    cursor.execute(query, (username, id))
    data = cursor.fetchall()
    error = None
    if(data):
        ins = 'UPDATE rsvp SET response = %s WHERE userName =%s AND eID = %s ' 
        cursor.execute(ins, (rsvp, username, id))
        conn.commit()
        cursor.close()
        return redirect(url_for('home'))
    else:
        ins = 'INSERT INTO rsvp VALUES(%s, %s, %s)'
        cursor.execute(ins, (username, id, rsvp))
        conn.commit()
        cursor.close()
        return redirect(url_for('home'))

#logout page
@app.route('/logout')
def logout():
    session.pop('username')
    return redirect('/')

@app.route('/recipeimages', methods=['GET', 'POST'])
def recipeimages():
    username = session['username']
    cursor = conn.cursor()
    query = 'SELECT * FROM recipe Where postedBy = %s'
    cursor.execute(query, (username))
    data = cursor.fetchall()
    if(data):
        return render_template('recipeimages.html', redata = data, username=username)
    else:
        error = "You have no recipe's to choose from"
        return render_template('post.html', error=error)


@app.route('/recipeimages2', methods=['GET', 'POST'])
def recipeimages2():
    username = session['username']
    recipe = request.args['recipe']
    global recipe4imageupload
    recipe4imageupload = recipe
    return render_template('recipeimages2.html', username=username, recipe = recipe)

@app.route('/recipeupload', methods=['GET', 'POST'])
def recipeupload():
    username = session['username']
    if request.method == 'POST':
        f = request.files['file']
        upload = cloudinary.uploader.upload(f)
        url = upload['secure_url']
        cursor = conn.cursor()
        ins = 'INSERT INTO recipepicture VALUES(%s,%s)'
        cursor.execute(ins, (recipe4imageupload, url))
        conn.commit()
        cursor.close()
    return redirect(url_for('home'))

@app.route('/eventimages', methods=['GET', 'POST'])
def eventimages():
    username = session['username']
    cursor = conn.cursor()
    query = 'SELECT * FROM event WHERE event.gCreator = %s'
    cursor.execute(query, (username))
    data = cursor.fetchall()
    if(data):
        return render_template('eventimages.html', redata = data, username=username)
    else:
        error="You have created no events and thus can't add any photos to an event."
        return render_template('group.html', error=error)

@app.route('/eventimages2', methods=['GET', 'POST'])
def eventimages2():
    username = session['username']
    event = request.args['event']
    global event4imageupload
    event4imageupload = event
    return render_template('eventimages2.html', username=username, event = event)

@app.route('/eventupload', methods=['GET', 'POST'])
def eventupload():
    username = session['username']
    if request.method == 'POST':
        f = request.files['file']
        upload = cloudinary.uploader.upload(f)
        url = upload['secure_url']
        cursor = conn.cursor()
        ins = 'INSERT INTO eventpicture VALUES(%s,%s)'
        cursor.execute(ins, (event4imageupload, url))
        conn.commit()
        cursor.close()
    return redirect(url_for('home'))

@app.route('/profile', methods=['GET', 'POST'])
def profile():
    username = session['username']
    cursor = conn.cursor()
    query = 'SELECT * FROM person WHERE person.userName = %s'
    cursor.execute(query, (username))
    data = cursor.fetchall()
    return render_template('profile.html', redata = data, username=username)

@app.route('/profileupdate', methods=['GET', 'POST'])
def profileupdate():
    username = session['username']
    fname = request.args['fname']
    lname = request.args['lname']
    email = request.args['email']
    profile = request.args['profile']
    if (fname):
        cursor = conn.cursor()
        query = 'UPDATE person SET fName = %s WHERE userName = %s'
        cursor.execute(query, (fname, username))
        conn.commit()
        cursor.close()
    if (lname):
        cursor = conn.cursor()
        query = 'UPDATE person SET lName = %s WHERE userName = %s'
        cursor.execute(query, (lname, username))
        conn.commit()
        cursor.close()
    if (email):
        cursor = conn.cursor()
        query = 'UPDATE person SET email = %s WHERE userName = %s'
        cursor.execute(query, (email, username))
        conn.commit()
        cursor.close()
    if (profile):
        cursor = conn.cursor()
        query = 'UPDATE person SET profile = %s WHERE userName = %s'
        cursor.execute(query, (profile, username))
        conn.commit()
        cursor.close()
    return redirect(url_for('home'))

#search 
@app.route('/searchperson', methods=['GET', 'POST'])
def searchperson():
    username = session['username']
    return render_template('searchperson.html', username=username)


@app.route('/searching2', methods=['GET', 'POST'])
def searching2():
    username = session['username']
    cursor = conn.cursor();
    filter = request.args['filter']
    filter = "%" + filter +"%"
    query = 'SELECT DISTINCT * FROM person WHERE person.fName LIKE %s OR person.lName LIKE %s OR person.email LIKE %s OR person.profile LIKE %s OR person.userName LIKE %s'
    cursor.execute(query, (filter, filter, filter, filter, filter))
    data = cursor.fetchall()
    conn.commit()
    cursor.close()
    if(data):
        return render_template('resultsperson.html', username=username, info=data)
    else:
        error="No results found"
        return render_template('searchperson.html', error=error)

#display page
@app.route('/display2', methods=['GET', 'POST'])
def display2():
    username = session['username']
    id = request.args['id']
    cursor = conn.cursor()
    query = 'SELECT person.fName, person.lName, person.userName, person.email, person.profile FROM person WHERE person.userName = %s'
    cursor.execute(query, (id))
    data = cursor.fetchall()
    return render_template('display2.html', redata = data, username=username)

@app.route('/eventlist', methods=['GET', 'POST'])
def eventlist():
    username = session['username']
    cursor = conn.cursor();
    query = 'SELECT * FROM event INNER JOIN groupmembership ON event.gName = groupmembership.gName WHERE groupmembership.memberName = %s AND event.eDate >= CURRENT_TIMESTAMP()'
    cursor.execute(query, (username))
    data = cursor.fetchall()
    cursor.close()
    if(data):
        return render_template('eventlist.html', username=username, info=data)
    else:
        error="You have no events coming up for the groups you're involved in."
        return render_template('group.html', error=error)

#display page
@app.route('/display3', methods=['GET', 'POST'])
def display3():
    username = session['username']
    id = request.args['id']
    cursor = conn.cursor()
    query = 'SELECT * FROM event WHERE eID = %s'
    cursor.execute(query, (id))
    data = cursor.fetchall()
    query = 'SELECT * FROM rsvp WHERE eID = %s AND response = 1'
    cursor.execute(query, (id))
    data2 = cursor.fetchall()
    query = 'SELECT * FROM eventpicture WHERE eID = %s'
    cursor.execute(query, (id))
    data3 = cursor.fetchall()
    return render_template('display3.html', edata = data, rdata = data2, pdata = data3, username=username)

#step page
@app.route('/remove', methods=['GET', 'POST'])
def remove():
    username = session['username']
    cursor = conn.cursor();
    query = 'SELECT * FROM recipe Where postedBy = %s'
    cursor.execute(query, (username))
    data = cursor.fetchall()
    cursor.close()
    if(data):
        return render_template('remove.html', sdata=data, username=username)
    else:
        error = "You have no recipe's to choose from."
        return render_template('post.html', error=error)

#step page
@app.route('/recipe_edit', methods=['GET', 'POST'])
def recipe_edit():
    username = session['username']
    recipe = request.args['recipe']
    global recipe4removal
    recipe4removal = recipe
    id = request.args['type']
    if id == 'tag':
        cursor = conn.cursor();
        query = 'SELECT * FROM recipetag Where recipeID = %s'
        cursor.execute(query, (recipe))
        data = cursor.fetchall()
        cursor.close()
        if(data):
            return render_template('remove_tag.html', sdata=data, username=username)
        else:
            error = "You have no tag's for this recipe to choose from."
            return render_template('post.html', error=error)
    if id == 'image':
        cursor = conn.cursor();
        query = 'SELECT * FROM recipepicture Where recipeID = %s'
        cursor.execute(query, (recipe))
        data = cursor.fetchall()
        cursor.close()
        if(data):
            return render_template('remove_image.html', sdata=data, username=username)
        else:
            error = "You have no image's for this recipe to choose from."
            return render_template('post.html', error=error)
    if id == 'ingredient':
        cursor = conn.cursor();
        query = 'SELECT * FROM recipeingredient Where recipeID = %s'
        cursor.execute(query, (recipe))
        data = cursor.fetchall()
        cursor.close()
        if(data):
            return render_template('remove_ingredient.html', sdata=data, username=username)
        else:
            error = "You have no ingredient's for this recipe to choose from."
            return render_template('post.html', error=error)
    if id == 'step':
        cursor = conn.cursor();
        query = 'SELECT * FROM step Where recipeID = %s'
        cursor.execute(query, (recipe))
        data = cursor.fetchall()
        cursor.close()
        if(data):
            return render_template('remove_step.html', sdata=data, username=username)
        else:
            error = "You have no step's for this recipe to choose from."
            return render_template('post.html', error=error)
    if id == 'recipe':
        cursor = conn.cursor();
        query = 'DELETE FROM relatedrecipe WHERE recipe2 = %s'
        cursor.execute(query, (recipe))
        conn.commit()
        query = 'DELETE FROM relatedrecipe WHERE recipe1 = %s'
        cursor.execute(query, (recipe))
        conn.commit()
        query = 'DELETE FROM reviewpicture WHERE recipeID = %s'
        cursor.execute(query, (recipe))
        conn.commit()
        query = 'DELETE FROM review WHERE recipeID = %s'
        cursor.execute(query, (recipe))
        conn.commit()
        query = 'DELETE FROM recipetag WHERE recipeID = %s'
        cursor.execute(query, (recipe))
        conn.commit()
        query = 'DELETE FROM recipeingredient WHERE recipeID = %s'
        cursor.execute(query, (recipe))
        conn.commit()
        query = 'DELETE FROM step WHERE recipeID = %s'
        cursor.execute(query, (recipe))
        conn.commit()
        query = 'DELETE FROM recipepicture WHERE recipeID = %s'
        cursor.execute(query, (recipe))
        conn.commit()
        query = 'DELETE FROM recipe WHERE recipeID = %s'
        cursor.execute(query, (recipe))
        conn.commit()
        cursor.close()
        return redirect(url_for('home'))

#adding a step page
@app.route('/tag_edit', methods=['GET', 'POST'])
def tag_edit():
    username = session['username']
    tag = request.args['tag']
    cursor = conn.cursor()
    query = 'DELETE FROM recipetag WHERE recipeID = %s AND tagText = %s'
    cursor.execute(query, (recipe4removal, tag))
    conn.commit()
    cursor.close()
    return redirect(url_for('home'))

#adding a step page
@app.route('/ingredient_edit', methods=['GET', 'POST'])
def ingredient_edit():
    username = session['username']
    ingred = request.args['ingred']
    cursor = conn.cursor()
    query = 'DELETE FROM recipeingredient WHERE recipeID = %s AND iName = %s'
    cursor.execute(query, (recipe4removal, ingred))
    conn.commit()
    cursor.close()
    return redirect(url_for('home'))

#adding a step page
@app.route('/step_edit', methods=['GET', 'POST'])
def step_edit():
    username = session['username']
    step = request.args['step']
    cursor = conn.cursor()
    query = 'DELETE FROM step WHERE recipeID = %s AND stepNo = %s'
    cursor.execute(query, (recipe4removal, step))
    conn.commit()
    cursor.close()
    return redirect(url_for('home'))

#adding a step page
@app.route('/image_edit', methods=['GET', 'POST'])
def image_edit():
    username = session['username']
    image = request.args['image']
    cursor = conn.cursor()
    query = 'DELETE FROM recipepicture WHERE recipeID = %s AND pictureURL = %s'
    cursor.execute(query, (recipe4removal, image))
    conn.commit()
    cursor.close()
    return redirect(url_for('home'))

#step page
@app.route('/removee', methods=['GET', 'POST'])
def removee():
    username = session['username']
    cursor = conn.cursor();
    query = 'SELECT DISTINCT gName FROM `group` Where gCreator = %s'
    cursor.execute(query, (username))
    data = cursor.fetchall()
    cursor.close()
    if(data):
        return render_template('removee.html', sdata=data, username=username)
    else:
        error="You have no groups you created and therefore no groups or events to remove."
        return render_template('group.html', error=error)

#step page
@app.route('/group_edit', methods=['GET', 'POST'])
def group_edit():
    username = session['username']
    group = request.args['group']
    id = request.args['type']
    if id == 'event':
        cursor = conn.cursor();
        query = 'SELECT * FROM event Where gName = %s AND gCreator = %s'
        cursor.execute(query, (group, username))
        data = cursor.fetchall()
        cursor.close()
        if(data):
            return render_template('remove_event.html', sdata=data, username=username)
        else:
            error="You have no events for this group."
            return render_template('group.html', error=error)
    if id == 'group':
        cursor = conn.cursor()
        query = 'DELETE FROM rsvp WHERE eID IN (SELECT eID FROM event Where gName = %s AND gCreator =%s)'
        cursor.execute(query, (group, username))
        conn.commit()
        query = 'DELETE FROM eventpicture WHERE eID IN (SELECT eID FROM event Where gName = %s AND gCreator =%s)'
        cursor.execute(query, (group, username))
        conn.commit()
        query = 'DELETE FROM event WHERE eID IN (SELECT eID FROM (SELECT * FROM event) AS x Where gName = %s AND gCreator =%s)'
        cursor.execute(query, (group, username))
        conn.commit()
        query = 'DELETE FROM groupmembership WHERE gName = %s AND gCreator =%s'
        cursor.execute(query, (group, username))
        conn.commit()
        query = 'DELETE FROM `group` WHERE gName = %s AND gCreator =%s'
        cursor.execute(query, (group, username))
        conn.commit()
        conn.commit()
        cursor.close()
        return redirect(url_for('home'))

#adding a step page
@app.route('/event_edit', methods=['GET', 'POST'])
def event_edit():
    username = session['username']
    event = request.args['name']
    cursor = conn.cursor()
    query = 'DELETE FROM rsvp WHERE eID = %s'
    cursor.execute(query, (event))
    conn.commit()
    query = 'DELETE FROM eventpicture WHERE eID = %s'
    cursor.execute(query, (event))
    conn.commit()
    query = 'DELETE FROM event WHERE eID = %s'
    cursor.execute(query, (event))
    conn.commit()
    cursor.close()
    return redirect(url_for('home'))

#step page
@app.route('/leave', methods=['GET', 'POST'])
def leave():
    username = session['username']
    cursor = conn.cursor();
    query = 'SELECT * FROM groupmembership Where memberName = %s'
    cursor.execute(query, (username))
    data = cursor.fetchall()
    cursor.close()
    if(data):
        return render_template('leave.html', sdata=data, username=username)
    else:
        error="You are not apart of any groups right now and therefore cannot leave any."
        return render_template('group.html', error=error)

#step page
@app.route('/leave_group', methods=['GET', 'POST'])
def leave_group():
    username = session['username']
    group = request.args['group']
    l1=list(group.split(","))
    gname = l1[0]
    gcreator = l1[1]
    if(gcreator==username):
        error = "You cannot leave this group as you are the owner, please remove this group instead."
        return render_template('group.html', error = error)
    else:
        cursor = conn.cursor();
        query = 'DELETE FROM groupmembership Where memberName = %s AND gName = %s AND gCreator = %s'
        cursor.execute(query, (username, gname, gcreator))
        conn.commit()
        query = 'DELETE FROM rsvp WHERE eID IN (SELECT eID FROM `event` WHERE gName = %s AND gCreator = %s) AND userName = %s'
        cursor.execute(query, (gname, gcreator, username))
        conn.commit()
        data = cursor.fetchall()
        cursor.close()
        return redirect(url_for('home'))

#recipe page
@app.route('/review', methods=['GET', 'POST'])
def review():
    username = session['username']
    cursor = conn.cursor();
    query = 'SELECT * FROM recipe'
    cursor.execute(query)
    data = cursor.fetchall()
    cursor.close()
    if(data): 
        return render_template('review.html', sdata=data, username=username)
    else:
        error="There are no recipes to choose from."
        return render_template('post.html', error=error)

#Submit recipe
@app.route('/add_review', methods=['GET', 'POST'])
def add_review():
    username = session['username']
    id = request.args['review']
    title = request.args['rtitle']
    rdesc = request.args['rdesc']
    stars = request.args['stars']
    cursor = conn.cursor()
    query = 'SELECT * FROM review WHERE recipeID = %s AND userName = %s'
    cursor.execute(query, (id, username))
    data = cursor.fetchall()
    error = None
    if(stars.isnumeric()):
        if(data):
            error = "You already have a review for this recipe."
            return render_template('post.html', error = error)
        else:
            ins = 'INSERT INTO review VALUES(%s, %s, %s, %s, %s)'
            cursor.execute(ins, (username, id, title, rdesc, stars))
            conn.commit()
            cursor.close()
            return redirect(url_for('home'))
    else:
        error = "Stars needs to be a number."
        return render_template('post.html', error = error)

@app.route('/reviewimages', methods=['GET', 'POST'])
def reviewimages():
    username = session['username']
    cursor = conn.cursor();
    query = 'SELECT * FROM review WHERE userName=%s'
    cursor.execute(query,(username))
    data = cursor.fetchall()
    cursor.close()
    if(data):
        return render_template('reviewimages.html', sdata=data, username=username)
    else:
        error="You have no review's to choose from"
        return render_template('post.html', error=error)

@app.route('/reviewimages2', methods=['GET', 'POST'])
def reviewimages2():
    username = session['username']
    id = request.args['recipe']
    global review4imageupload
    review4imageupload = id
    return render_template('reviewimages2.html', recipe = id, username=username)


@app.route('/reviewupload', methods=['GET', 'POST'])
def reviewupload():
    username = session['username']
    if request.method == 'POST':
        f = request.files['file']
        upload = cloudinary.uploader.upload(f)
        url = upload['secure_url']
        cursor = conn.cursor()
        ins = 'INSERT INTO reviewpicture VALUES(%s,%s,%s)'
        cursor.execute(ins, (username,review4imageupload, url))
        conn.commit()
        cursor.close()
    return redirect(url_for('home'))

#search 
@app.route('/reviewsearch', methods=['GET', 'POST'])
def reviewsearch():
    username = session['username']
    cursor = conn.cursor();
    query = 'SELECT * FROM recipe'
    cursor.execute(query)
    data = cursor.fetchall()
    cursor.close()
    if(data):
        return render_template('reviewsearch.html', username=username, sdata=data)
    else:
        error="There are no recipes to choose from."
        return render_template('post.html', error=error)

#search 
@app.route('/displayreviews', methods=['GET', 'POST'])
def isplayreviews():
    username = session['username']
    id = request.args['recipe']
    cursor = conn.cursor();
    query = 'SELECT * FROM review WHERE recipeID =%s'
    cursor.execute(query,(id))
    data = cursor.fetchall()
    query = 'SELECT * FROM reviewpicture WHERE recipeID =%s'
    cursor.execute(query,(id))
    data2 = cursor.fetchall()
    cursor.close()
    return render_template('displayreviews.html', username=username, sdata=data, imdata=data2)

@app.route('/removereview', methods=['GET', 'POST'])
def removereview():
    username = session['username']
    cursor = conn.cursor()
    query = 'SELECT * FROM review WHERE userName = %s ORDER BY revTitle'
    cursor.execute(query, (username))
    data = cursor.fetchall()
    error = None
    if(data):
        return render_template('removereview.html', sdata=data, error = error)
    else:
        error = "You have no review's to choose from."
        return render_template('post.html', error=error)

#step page
@app.route('/remove_review', methods=['GET', 'POST'])
def remove_review():
    username = session['username']
    group = request.args['group']
    cursor = conn.cursor();
    query = 'DELETE FROM reviewpicture Where userName = %s AND recipeID = %s'
    cursor.execute(query, (username, group))
    conn.commit()
    query = 'DELETE FROM review Where userName = %s AND recipeID = %s'
    cursor.execute(query, (username, group))
    conn.commit()
    cursor.close()
    return redirect(url_for('home'))

@app.route('/restriction', methods=['GET', 'POST'])
def restriction():
    username = session['username']
    cursor = conn.cursor()
    query = 'SELECT * FROM ingredient'
    cursor.execute(query)
    data = cursor.fetchall()
    error = None
    if(data):
        return render_template('restriction.html', sdata=data, error = error)
    else:
        error = "There are no ingredient's to choose from."
        return render_template('post.html', error=error)

@app.route('/add_restriction', methods=['GET', 'POST'])
def add_restriction():
    username = session['username']
    recipe = request.args['recipe']
    Description = request.args['Description']
    cursor = conn.cursor()
    query = 'SELECT * FROM restrictions WHERE iName = %s AND restrictionDesc = %s'
    cursor.execute(query, (recipe, Description))
    data = cursor.fetchall()
    error = None
    if(data):
        error = "This restriction for this ingredient already exists."
        return render_template('post.html', error = error)
    else:
        ins = 'INSERT INTO restrictions VALUES(%s, %s)'
        cursor.execute(ins, (recipe, Description))
        conn.commit()
        cursor.close()
        return redirect(url_for('home'))

@app.route('/related', methods=['GET', 'POST'])
def related():
    username = session['username']
    cursor = conn.cursor();
    query = 'SELECT * FROM recipe WHERE PostedBy=%s'
    cursor.execute(query,(username))
    data = cursor.fetchall()
    cursor.close()
    if(data):
        return render_template('related.html', sdata=data, username=username)
    else:
        error="You have no review's to choose from"
        return render_template('post.html', error=error)

#adding a step page
@app.route('/similar', methods=['GET', 'POST'])
def similar():
    username = session['username']
    global choosenrecipe
    recipe = request.args['recipe']
    choosenrecipe = recipe
    cursor = conn.cursor()
    query = 'SELECT * FROM recipe WHERE recipeID!=%s'
    cursor.execute(query, (recipe))
    data = cursor.fetchall()
    cursor.close()
    if(data):
        return render_template('choose.html', sdata=data, username=username)
    else:
        error="There are no other recipe's to choose from."
        return render_template('post.html', error=error)

@app.route('/add_similar', methods=['GET', 'POST'])
def add_similar():
    username = session['username']
    recipe = request.args['recipe']
    cursor = conn.cursor()
    query = 'SELECT * FROM relatedrecipe WHERE recipe1 = %s AND recipe2 = %s'
    cursor.execute(query, (choosenrecipe, recipe))
    data = cursor.fetchall()
    error = None
    if(data):
        error = "These recieps are already marked as similar."
        return render_template('post.html', error = error)
    else:
        ins = 'INSERT INTO relatedrecipe VALUES(%s, %s)'
        cursor.execute(ins, (choosenrecipe, recipe))
        conn.commit()
        ins = 'INSERT INTO relatedrecipe VALUES(%s, %s)'
        cursor.execute(ins, (recipe, choosenrecipe))
        conn.commit()
        cursor.close()
        return redirect(url_for('home'))


app.secret_key = 'some key that you will never guess'

if __name__ == "__main__":
    app.run('127.0.0.1', 5000, debug = True)
