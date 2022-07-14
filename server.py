# Author : Nemuel Wainaina

from datetime import datetime as dt
from flask import Flask, render_template, request, redirect, url_for
from random import randint
from werkzeug.utils import secure_filename
import os
import psycopg2 as psy

app = Flask(__name__)

# create and return connection and cursor objects to the database
def dbConnect():
    conn = psy.connect(
        database="blog",
        user="postgres",
        password="password123"
    )
    curs = conn.cursor()
    return conn, curs

# current date in the format DD/MM/YYYY
def currentDt():
    x = dt.now()
    return x.strftime('%d') + '/' + x.strftime('%m') + '/' + x.strftime('%Y')

# generate and return a unique post_id
def generate_post_id():
    conn, curs = dbConnect()
    rand = randint(111111, 999999)
    q = 'SELECT post_id FROM posts;'
    curs.execute(q)
    items = curs.fetchall()
    if len(items) != 0:
        # check whether the randomly generated ID already exists, if so, 
        # perform a recursive function call to regenerate the ID and return it
        ids = [item[0] for item in items]
        if rand in ids:
            generate_post_id()
        else: 
            return rand
    else:
        # this is the first post whose ID we are generating , so just return the random ID we generated
        return rand
    
# landing page for regular visitors
@app.route('/')
def index():
    q = 'SELECT * FROM posts;'
    conn, curs = dbConnect()
    curs.execute(q)
    posts = curs.fetchall()
    curs.close()
    conn.close()
    
    return render_template('index.html', posts=posts)

# page for viewing a post by regular visitors
@app.route('/post/<post_id>/')
def post(post_id):
    q = 'SELECT * FROM posts WHERE post_id=%s;'
    conn, curs = dbConnect()
    curs.execute(q, (post_id,))
    post = curs.fetchone()
    if post is None:
        return redirect(url_for('index'))
    curs.close()
    conn.close()
    return render_template('post.html', post=post)

# comment on a blog post
@app.route('/addcomment/<post_id>/', methods=['POST'])
def addcomment(post_id):
    name = request.form['name']
    comment = request.form['comment']
    dt = currentDt()
    conn, curs = dbConnect()
    q = 'INSERT INTO comments VALUES(%s, %s, %s, %s);'
    curs.execute(q, (post_id, dt, name, comment))
    conn.commit()
    return redirect(url_for('post', post_id=post_id))

# admin's login page
@app.route('/admin/', methods=['POST', 'GET'])
def admin():
    if request.method == 'POST':
        usrnm = request.form['usrnm']
        passwd = request.form['passwd']
        if usrnm == 'admin' and passwd == 'password123':
            return redirect(url_for('home'))
        else:
            msg = 'Invalid credentials !'
            return render_template('login.html', msg=msg)
    else:
        return render_template('login.html')

# admin's home page, a list of posts as well
@app.route('/home/')
def home():
    q = 'SELECT * FROM posts;'
    conn, curs = dbConnect()
    curs.execute(q)
    posts = curs.fetchall()
    curs.close()
    conn.close()
    
    return render_template('home.html', posts=posts)

# page for viewing a post by the admin
@app.route('/postx/<post_id>/')
def postx(post_id):
    conn, curs = dbConnect()
    q = 'SELECT * FROM posts WHERE post_id=%s;'
    curs.execute(q, (post_id,))
    post = curs.fetchone()
    if post is None:
        return redirect(url_for('index'))
    q = 'SELECT * FROM comments WHERE post_id=%s;'
    curs.execute(q, (post_id,))
    comments = curs.fetchall()
    curs.close()
    conn.close()
    return render_template('postx.html', post=post, comments=comments)

# add a new post
@app.route('/addpost/', methods=['POST', 'GET'])
def addpost():
    if request.method == 'POST':
        img = request.files['img']
        title = request.form['title']
        content = request.form['content']
        post_dt = currentDt()
        img_path = secure_filename(img.filename)
        if not os.getcwd().endswith('\static\images'):
            os.chdir('./static/images/')
        img.save(img_path)
        post_id = generate_post_id()
        q = 'INSERT INTO posts VALUES(%s, %s, %s, %s, %s);'
        conn, curs = dbConnect()
        curs.execute(q, (post_id, post_dt, img_path, title, content))
        conn.commit()
        curs.close()
        conn.close()
        return render_template('newpost.html')
    else:
        return render_template('newpost.html')

# the route to update an existing post
@app.route('/editpost/<post_id>/', methods=['GET'])
def editpost(post_id):
    conn, curs = dbConnect()
    q = 'SELECT * FROM posts WHERE post_id=%s;'
    curs.execute(q, (post_id,))
    post = curs.fetchone()
    curs.close()
    conn.close()
    if post is not None:
        return render_template('editpost.html', post=post)
    return redirect(url_for('home'))

@app.route('/updatepost/', methods=['POST'])
def updatepost():
    post_id = request.form['post_id']
    title = request.form['title']
    content = request.form['content']
    post_dt = currentDt()

    conn, curs = dbConnect()

    q = 'SELECT image_path FROM posts WHERE post_id=%s;'
    curs.execute(q, (post_id,))
    img0 = curs.fetchone()[0]

    if request.files['img']:
        img = request.files['img']
        os.chdir('.\\static\\images')
        if os.path.exists(img0):
            os.remove(img0)
        img_path = secure_filename(img.filename)
        img.save(img_path)
        img0 = img_path

    q = 'UPDATE posts SET post_dt=%s, image_path=%s, title=%s, content=%s WHERE post_id=%s;'
    
    curs.execute(q, (post_dt, img0, title, content, post_id))
    conn.commit()
    curs.close()
    conn.close()
    return redirect(url_for('postx', post_id=post_id))

@app.route('/deletepost/<post_id>/')
def deletepost(post_id):
    conn, curs = dbConnect()
    q = 'SELECT image_path FROM posts WHERE post_id=%s;'
    curs.execute(q, (post_id,))
    img = curs.fetchone()[0]
    if not os.getcwd().endswith('\static\images'):
        os.chdir('./static/images/')        
    os.remove(img) # delete the post's image
    q = 'DELETE FROM comments WHERE post_id=%s;'
    curs.execute(q, (post_id,)) # delete comments on the post as well
    conn.commit()
    q = 'DELETE FROM posts WHERE post_id=%s;'
    curs.execute(q, (post_id,)) # finally delete the post itself
    conn.commit()

    curs.close()
    conn.close()

    return redirect(url_for('home'))

if __name__ == '__main__':
    app.run(debug=True)