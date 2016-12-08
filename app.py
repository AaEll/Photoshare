######################################
# skeleton author ben lawson <balawson@bu.edu> 
# Edited by: Craig Einstein <einstein@bu.edu>
# Edited by: Sarah Ferry <ferrys@bu.edu>
######################################
# Some code adapted from 
# CodeHandBook at http://codehandbook.org/python-web-application-development-using-flask-and-mysql/
# and MaxCountryMan at https://github.com/maxcountryman/flask-login/
# and Flask Offical Tutorial at  http://flask.pocoo.org/docs/0.10/patterns/fileuploads/
# see links for further understanding
###################################################

import flask
from flask import Flask, Response, request, render_template, redirect, url_for
from flaskext.mysql import MySQL
import flask.ext.login as flask_login
import time 
#for image uploading
from werkzeug import secure_filename
import os, base64

mysql = MySQL()
app = Flask(__name__)
app.secret_key = 'super secret string'  # Change this!

#These will need to be changed according to your creditionals
app.config['MYSQL_DATABASE_USER'] = 'root'
app.config['MYSQL_DATABASE_PASSWORD'] = 'applesauce5'
app.config['MYSQL_DATABASE_DB'] = "photoshare"
app.config['MYSQL_DATABASE_HOST'] = '127.0.0.1'
mysql.init_app(app)

#begin code used for login
login_manager = flask_login.LoginManager()
login_manager.init_app(app)

conn = mysql.connect()
cursor = conn.cursor()
cursor.execute("SELECT email from Users") 
users = cursor.fetchall()

def getUserList():
	cursor = conn.cursor()
	cursor.execute("SELECT email from Users") 
	return cursor.fetchall()

class User(flask_login.UserMixin):
	pass

@login_manager.user_loader
def user_loader(email):
	users = getUserList()
	if not(email) or email not in str(users):
		return
	user = User()
	user.id = email
	return user

@login_manager.request_loader
def request_loader(request):
	users = getUserList()
	email = request.form.get('email')
	if not(email) or email not in str(users):
		return
	user = User()
	user.id = email
	cursor = mysql.connect().cursor()
	cursor.execute("SELECT password FROM Users WHERE email = '{0}'".format(email))
	data = cursor.fetchall()
	pwd = str(data[0][0] )
	user.is_authenticated = request.form['password'] == pwd 
	return user

'''
A new page looks like this:
@app.route('new_page_name')
def new_page_function():
	return new_page_html
'''

@app.route('/login', methods=['GET', 'POST'])
def login():
	if flask.request.method == 'GET':
		return '''
			   <form action='login' method='POST'>
				<input type='text' name='email' id='email' placeholder='email'></input>
				<input type='password' name='password' id='password' placeholder='password'></input>
				<input type='submit' name='submit'></input>
			   </form></br>
		   <a href='/'>Home</a>
			   '''
	#The request method is POST (page is recieving data)
	email = flask.request.form['email']
	cursor = conn.cursor()
	#check if email is registered
	if cursor.execute("SELECT password FROM Users WHERE email = '{0}'".format(email)):
		data = cursor.fetchall()
		pwd = str(data[0][0] )
		if flask.request.form['password'] == pwd:
			user = User()
			user.id = email
			flask_login.login_user(user) #okay login in user
			return flask.redirect(flask.url_for('protected')) #protected is a function defined in this file

	#information did not match
	return "<a href='/login'>Try again</a>\
			</br><a href='/register'>or make an account</a>"

@app.route('/logout')
def logout():
	flask_login.logout_user()
	return render_template('hello.html', message='Logged out', users=findTopUsers()) 

@login_manager.unauthorized_handler
def unauthorized_handler():
	return render_template('unauth.html') 

#you can specify specific methods (GET/POST) in function header instead of inside the functions as seen earlier
@app.route("/register", methods=['GET'])
def register():
	return render_template('register.html', supress='True')  

@app.route("/register", methods=['POST'])
def register_user():
	try:
		email=request.form.get('email')
		password=request.form.get('password')
		first_name=request.form.get('first_name')
		last_name=request.form.get('last_name')
		if request.form.get("hometown"):
			hometown = request.form.get("hometown")
		else:
			hometown = "NULL"
		if request.form.get("gender"):
			gender = request.form.get("gender")
		else:
			gender = None
		dob=request.form.get("dob")
	except:
		print "couldn't find all tokens" #this prints to shell, end users will not see this (all print statements go to shell)
		return flask.redirect(flask.url_for('register'))
	cursor = conn.cursor()
	test =  isEmailUnique(email)
	if test:
		if gender:
			cursor.execute("INSERT INTO Users (first_name, last_name, dob, email, password, hometown, gender) VALUES ('{0}', '{1}', '{2}', '{3}', '{4}', '{5}', '{6}')".format(first_name, last_name, dob, email, password, hometown, gender))
		else:
			cursor.execute("INSERT INTO Users (first_name, last_name, dob, email, password, hometown) VALUES ('{0}', '{1}', '{2}', '{3}', '{4}', '{5}')".format(first_name, last_name, dob, email, password, hometown))

		conn.commit()
		#log user in
		user = User()
		user.id = email
		flask_login.login_user(user)
		return render_template('profile.html', name=first_name, message='Account Created!')
	else:
		print "couldn't find all tokens"
		return render_template("register.html", suppress=False)

def getUserIdFromEmail(email):
	cursor = conn.cursor()
	if cursor.execute("SELECT user_id  FROM Users WHERE email = '{0}'".format(email)):
		return cursor.fetchone()[0]
	else:
		return None

def isEmailUnique(email):
	#use this to check if a email has already been registered
	cursor = conn.cursor()
	if cursor.execute("SELECT email  FROM Users WHERE email = '{0}'".format(email)): 
		#this means there are greater than zero entries with that email
		return False
	else:
		return True
#end login code


@app.route('/profile')
@flask_login.login_required
def protected():
	uid = getUserIdFromEmail(flask_login.current_user.id)
	return render_template('profile.html', name=getFirstName(uid), message="Here's your profile")


def getFirstName(uid):
	cursor = conn.cursor()
	cursor.execute("SELECT first_name FROM Users WHERE user_id ='{0}'".format(uid))
	return cursor.fetchall()[0][0]

#begin photo uploading code
# photos uploaded using base64 encoding so they can be directly embeded in HTML 
ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg', 'gif'])
def allowed_file(filename):
	return '.' in filename and filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS

@app.route('/create_album', methods=['GET', 'POST'])
@flask_login.login_required
def create_album():
	if request.method == 'POST':
		uid = getUserIdFromEmail(flask_login.current_user.id)
		album_title = request.form.get('album_title')
		print(album_title)
		if isAlbumTitleUnique(album_title):
			cursor = conn.cursor()
			date = time.strftime("%Y-%m-%d")
			cursor.execute("INSERT INTO Album (album_title, user_id, date_of_creation) VALUES('{0}', '{1}', '{2}')".format(album_title,uid,date))
			conn.commit()
			return render_template('profile.html', name=getFirstName(uid), message='Album Created!!', albums=getUsersAlbums(uid))
		else:
			return render_template('create_album.html', message="Pick a new title!")
	else:
		return render_template('create_album.html')

def deletePhoto(photo_id):
	cursor = conn.cursor()
	cursor.execute("DELETE FROM liked_pictures where picture_id = '{0}'".format(photo_id))
	conn.commit()
	cursor.execute("DELETE FROM commented_photos WHERE picture_id='{0}'".format(photo_id))
	conn.commit()
	cursor.execute("DELETE FROM tagged_photos WHERE picture_id='{0}'".format(photo_id))
	conn.commit()
	cursor.execute("DELETE FROM Pictures WHERE picture_id='{0}'".format(photo_id))
	conn.commit()


def isAlbumTitleUnique(album_title):
	cursor = conn.cursor()
	if cursor.execute("SELECT album_title FROM Album WHERE album_title = '{0}'".format(album_title)): 
		#this means there are greater than zero entries with that album_title
		return False
	else:
		return True

def getUsersAlbums(uid):
	cursor = conn.cursor()
	cursor.execute("SELECT album_title, date_of_creation FROM Album WHERE user_id='{0}'".format(uid))
	return cursor.fetchall()


@app.route('/upload', methods=['GET', 'POST'])
@flask_login.login_required
def upload_file():
	uid = getUserIdFromEmail(flask_login.current_user.id)
	if (getUsersAlbums(uid)):
		if request.method == 'POST':
			imgfile = request.files['photo']
			caption = request.form.get('caption')
			tags = str(request.form.get('tags')).split(' ')
			album_title = request.form.get('album_title')
			album_id = getAlbumIdFromTitle(album_title)

			photo_data = base64.standard_b64encode(imgfile.read())
			cursor = conn.cursor()
			if isAlbumTitleUnique(album_title)==False and userOwnsAlbum(uid, album_title) == True:
				cursor.execute("INSERT INTO Pictures (imgdata, user_id, caption, album_id) VALUES ('{0}', '{1}', '{2}', '{3}')".format(photo_data, uid, caption, album_id))
				conn.commit()
				##you can do this better
				photo_id = cursor.lastrowid
				addPhotoTags(tags, photo_id)
				return render_template('profile.html', name=getFirstName(uid), message='Photo uploaded!')
			else:
				return render_template('upload.html', message="Please pick a valid album.")
		else:
			return render_template('upload.html')
	else:
		return render_template('create_album.html', message="Please create an album first!")

def userOwnsAlbum(uid, album_title):
	cursor = conn.cursor()
	if cursor.execute("SELECT * FROM Album WHERE album_title = '{0}' AND user_id = '{1}'".format(album_title, uid)):
		return True
	else:
		return False

def getAlbumIdFromTitle(album_title):
	cursor = conn.cursor()
	cursor.execute("SELECT album_id FROM Album WHERE album_title = '{0}'".format(album_title))
	return cursor.fetchone()[0]

def addPhotoTags(tags, picture_id):
	cursor = conn.cursor()
	for i in tags:
		cursor.execute("INSERT INTO tagged_photos (word, picture_id) VALUES ('{0}', '{1}')".format(i, picture_id))
	conn.commit()

#end photo uploading code 

@app.route('/albums', methods=['GET', 'POST'])
def albums():
	uid = getUserIdFromEmail(flask_login.current_user.id)
	pix_with_tags_and_comments = []
	if request.method == 'POST':
		album_id = request.form.get('album_id')
		album_title = request.form["album_search"]
		#if request.form["Delete"]

		for i in getAlbumPhotos(album_id, uid):
			pix_with_tags_and_comments += [getTagsAndComments(i)]
		return render_template("show_all_photos.html", photos=pix_with_tags_and_comments, album_title=album_title)
	else:
		return render_template("albums.html", albums=showAlbums(uid))

def showAlbums(uid):
	cursor = conn.cursor()
	cursor.execute("SELECT album_title, album_id, date_of_creation FROM Album WHERE user_id = '{0}'".format(uid))
	return cursor.fetchall()

@app.route("/albums_delete", methods=['GET', "POST"])
@flask_login.login_required
def byeAlbum():
	print("hey!")
	uid = getUserIdFromEmail(flask_login.current_user.id)
	if request.method == 'POST':
		album_id = request.form.get('album_id')
		deleteAlbum(album_id, uid)		
		#if request.form["Delete"]
		return render_template("profile.html", message="Album deleted!!")
	else:
		return render_template("albums.html", albums=showAlbums(uid), message="Error deleting album")

def deleteAlbum(album_id, uid):
	cursor = conn.cursor()
	pix = getAlbumPhotos(album_id, uid)
	for pic in pix:
		deletePhoto(pic[1])
	cursor.execute("DELETE FROM Album WHERE album_id='{0}'".format(album_id))
	conn.commit()

def getAlbumPhotos(album_id, uid):
	cursor = conn.cursor()
	query = "SELECT P.imgdata, P.picture_id, P.caption, A.album_title FROM Pictures P, Album A WHERE A.album_id = P.album_id AND A.album_id = '{0}' AND A.user_id = '{1}'"
	cursor.execute(query.format(album_id, uid))
	return cursor.fetchall()

@app.route('/friends', methods=['GET', 'POST'])
@flask_login.login_required
def friends():
	uid = getUserIdFromEmail(flask_login.current_user.id)
	friends = getUsersFriends(uid)
	friends_names = []
	for i in friends:
		friends_names += [getUserName(i)]
	if request.method == 'POST':
		first_name = request.form.get('search_first_name')
		last_name = request.form.get('search_last_name')
		if searchUsers(first_name, last_name):
			return render_template('friends.html', friends=friends_names, users_search=searchUsers(first_name,last_name))
		else:
			return render_template('friends.html', friends=friends_names, message="No users with that name")
	else:
		return render_template('friends.html', friends=friends_names)

@app.route('/add_friends', methods=['GET','POST'])
@flask_login.login_required
def friendsAdd():
	uid = getUserIdFromEmail(flask_login.current_user.id)
	friends_names = []
	if request.method == 'POST':
		email = request.form.get('search_email')
		friend_uid = getUserIdFromEmail(email)
		if addFriend(friend_uid) == True:
			friends = getUsersFriends(uid)
			for i in friends:
				friends_names += [getUserName(i)]
			return render_template('friends.html', friends=friends_names, message="Friend Added!")
		else:
			friends = getUsersFriends(uid)
			for i in friends:
				friends_names += [getUserName(i)]
			return render_template('friends.html', friends=friends_names, message="Please pick a valid email")
	else:
		return render_template('add_friends.html')

def getUsersFriends(uid):
	cursor = conn.cursor()
	cursor.execute("SELECT user_id_friend FROM Friends_of WHERE user_id = '{0}'".format(uid))
	return cursor.fetchall()

def getUserName(uid):
	uid = uid[0]
	cursor = conn.cursor()
	cursor.execute("SELECT first_name, last_name FROM Users where user_id = '{0}'".format(uid))
	return cursor.fetchall()

def addFriend(friend_uid):
	uid = getUserIdFromEmail(flask_login.current_user.id)
	cursor = conn.cursor()
	if cursor.execute("SELECT user_id FROM Users WHERE user_id='{0}'".format(friend_uid)):
		cursor.execute("INSERT INTO friends_of(user_id, user_id_friend) VALUES ('{0}', '{1}')".format(uid, friend_uid))
		conn.commit()
		print("friend added!")
		return True
	else:
		return False

def searchUsers(first_name='', last_name=''):
	cursor = conn.cursor()
	first_name=str(first_name)
	last_name=str(last_name)
	if first_name != '' and (last_name == ''):
		cursor.execute("SELECT first_name, last_name, dob, email, user_id FROM Users WHERE first_name ='{0}'".format(first_name))
	elif last_name != '' and (first_name == ''):
		cursor.execute("SELECT first_name, last_name, dob, email, user_id FROM Users WHERE last_name ='{0}'".format(last_name))
	else:
		cursor.execute("SELECT first_name, last_name, dob, email, user_id FROM Users WHERE first_name = '{0}' AND last_name ='{1}'".format(first_name, last_name))
	return cursor.fetchall()

@app.route("/show_all_photos", methods=['POST', 'GET'])
def showPix():
	if flask_login.current_user.is_authenticated():
		uid = getUserIdFromEmail(flask_login.current_user.id)
	if request.method == 'POST':
		if request.form.get("comment"):
			comment = request.form.get("comment")
			photo_id = request.form.get("picture_id")
			if flask_login.current_user.is_authenticated():
				if (isCommentValid(photo_id, uid)):
					comment_id = addComment(comment, uid)
				else:
					return render_template("show_all_photos.html", photos=displayAllPicturesWithCommentsAndTags(), message="All photos. You cannot comment on your own photo.")
			else:
				comment_id = addComment(comment, -1)
			addCommentToPhoto(comment_id, photo_id)
			
			return render_template("show_all_photos.html", photos=displayAllPicturesWithCommentsAndTags(), message="All photos. Comment added!")
		elif request.form["photo_delete"]:
			photo_id = request.form.get("picture_id")
			if flask_login.current_user.is_authenticated():
				if currentUserOwnsPhoto(uid, photo_id):
					deletePhoto(photo_id)
					return render_template("show_all_photos.html", photos=displayAllPicturesWithCommentsAndTags(), message="Photo Deleted!")
				else:
					return render_template("show_all_photos.html", photos = displayAllPicturesWithCommentsAndTags(), message="You do not have permission to delete this photo.")
			else:
				return render_template("show_all_photos.html", photos = displayAllPicturesWithCommentsAndTags(), message="You do not have permission to delete this photo.")
		else:
			return render_template("show_all_photos.html", photos=displayAllPicturesWithCommentsAndTags(), message="All photos")
	else:
		return render_template("show_all_photos.html", photos=displayAllPicturesWithCommentsAndTags(), message="All photos")

@app.route("/show_my_photos", methods=["POST", "GET"])
@flask_login.login_required
def myPix():
	uid = getUserIdFromEmail(flask_login.current_user.id)
	pix = []
	for i in getUsersPhotos(uid):
		pix += [getTagsAndComments(i)]
	return render_template("show_all_photos.html", photos=pix)

@app.route("/like_pic", methods=["POST", "GET"])
@flask_login.login_required
def pics_liked():
	uid = getUserIdFromEmail(flask_login.current_user.id)
	pix = displayAllPicturesWithCommentsAndTags()
	if request.method == 'POST':
		picture_id = request.form.get("picture_id")
		if likeValid(uid, picture_id) == False:
			return render_template("show_all_photos.html", photos=pix, message="You've already liked this picture. Try again")
		else:
			likePic(uid, picture_id)
			pix = displayAllPicturesWithCommentsAndTags()
			return render_template("show_all_photos.html", photos=pix, message="Photo liked!! Here are all pictures")
	else:
		return render_template("show_all_photos.html", photos=pix, message="Error liking picture. Try again")


def likePic(uid, picture_id):
	cursor= conn.cursor()
	cursor.execute("INSERT INTO liked_pictures(user_id, picture_id) VALUES('{0}', '{1}')".format(uid, picture_id))
	conn.commit()

def likeValid(uid, picture_id):
	cursor = conn.cursor()
	if cursor.execute("SELECT user_id FROM liked_pictures WHERE user_id ='{0}' AND picture_id='{1}'".format(uid, picture_id)):
		return False
	else:
		return True

def getUsersPhotos(uid):
	cursor = conn.cursor()
	cursor.execute("SELECT P.imgdata, P.picture_id, P.caption, A.album_title FROM Pictures P, Album A WHERE P.album_id = A.album_id AND P.user_id = '{0}'".format(uid))
	return cursor.fetchall() 

def currentUserOwnsPhoto(uid, picture_id):
	cursor = conn.cursor()
	if cursor.execute("SELECT * FROM Pictures WHERE user_id = '{0}' AND picture_id = '{1}'".format(uid, picture_id)):
		return True
	else:
		return False

def displayAllPicturesWithCommentsAndTags():
	pix_with_tags_and_comments = []
	for i in getAllPhotos():
		pix_with_tags_and_comments += [getTagsAndComments(i)]
	return pix_with_tags_and_comments

def getTagsAndComments(photo):
	return [photo] + [getTags(photo[1])] + [getComments(photo[1])] + [getLikes(photo[1])] + [getUsersLiked(photo[1])]

def getLikes(picture_id):
	cursor = conn.cursor()
	cursor.execute("SELECT COUNT(picture_id) FROM liked_pictures WHERE picture_id ='{0}'".format(picture_id))
	return cursor.fetchall()

def getUsersLiked(picture_id):
	cursor = conn.cursor()
	cursor.execute("SELECT U.first_name, U.last_name FROM liked_pictures P, Users U WHERE U.user_id = P.user_id AND P.picture_id = '{0}'".format(picture_id))
	return cursor.fetchall()

def getAllPhotos():
	cursor = conn.cursor()
	cursor.execute("SELECT P.imgdata, P.picture_id, P.caption, A.album_title FROM Pictures P, Album A WHERE P.album_id = A.album_id")
	return cursor.fetchall()

def addComment(comment, uid):
	date = time.strftime("%Y-%m-%d")
	print(date)
	cursor = conn.cursor()
	cursor.execute("INSERT INTO Comment(text, user_id, date) VALUES ('{0}', '{1}', '{2}')".format(comment, uid, date))
	conn.commit()
	comment_id = cursor.lastrowid
	return comment_id

def addCommentToPhoto(comment_id, picture_id):
	cursor = conn.cursor()
	cursor.execute("INSERT INTO Commented_photos(comment_id, picture_id) VALUES('{0}', '{1}')".format(comment_id, picture_id))
	conn.commit()

def isCommentValid(picture_id, uid):
	cursor = conn.cursor()
	if cursor.execute("SELECT * FROM Pictures WHERE picture_id = '{0}' AND user_id='{1}'".format(picture_id, uid)):
		return False
	else:
		return True

def getComments(picture_id):
	cursor = conn.cursor()
	cursor.execute("SELECT C.text, U.first_name, U.last_name from Commented_photos CP, Comment C, Users U WHERE CP.comment_id = C.comment_id AND C.user_id = U.user_id AND CP.picture_id = '{0}' ORDER BY C.date".format(picture_id))
	return cursor.fetchall()

def getTags(picture_id):
	cursor = conn.cursor()
	cursor.execute("SELECT word FROM Tagged_photos WHERE picture_id = '{0}'".format(picture_id))
	return cursor.fetchall()

@app.route('/my_tag_search', methods=["POST", "GET"])
@flask_login.login_required
def searchMyTags():
	uid = getUserIdFromEmail(flask_login.current_user.id)
	pix_with_tags_and_comments = []
	pix = []
	for i in getUsersPhotos(uid):
		pix += [getTagsAndComments(i)]
	if request.method == "POST":
		tag = request.form.get('tag_name')
		for i in getUserTaggedPhotos(tag, uid):
			pix_with_tags_and_comments += [getTagsAndComments(i)]
		if pix_with_tags_and_comments:
			return render_template("show_all_photos.html", photos=pix_with_tags_and_comments)
		else:
			return render_template("show_all_photos.html", message="Sorry, none, try again!")
	else:
		return render_template("show_all_photos.html", photos=pix)


def getUserTaggedPhotos(tag, uid):
	cursor = conn.cursor()
	cursor.execute("SELECT P.imgdata, P.picture_id, P.caption, A.album_title FROM Pictures P, Album A, Tagged_photos T WHERE T.picture_id = P.picture_id AND P.album_id = A.album_id AND T.word = '{0}' AND P.user_id ='{1}'".format(tag, uid))
	return cursor.fetchall()

#####TAGS######
@app.route('/tag_search', methods=["POST", "GET"])
def searchTags():
	pix_with_tags_and_comments = []
	if request.method == "POST":
		if(request.form.get('tag_search')):
			tags = request.form.get('tag_search').split(" ")
			for i in getAllTaggedPhotos(tags):
				pix_with_tags_and_comments += [getTagsAndComments(i)]
		else:
			tag = request.form['common_tag']
			for i in getTaggedPhotos(tag):
				pix_with_tags_and_comments += [getTagsAndComments(i)]
		if pix_with_tags_and_comments:
			return render_template("show_all_photos.html", photos=pix_with_tags_and_comments)
		else:
			return render_template("tag_search.html", common=getMostCommonTags(), message="Sorry, none, try again!")
	else:
		return render_template("tag_search.html", common=getMostCommonTags())

def getTaggedPhotos(tag):
	cursor = conn.cursor()
	cursor.execute("SELECT P.imgdata, P.picture_id, P.caption, A.album_title FROM Pictures P, Album A, Tagged_photos T WHERE T.picture_id = P.picture_id AND P.album_id = A.album_id AND T.word = '{0}'".format(tag))
	return cursor.fetchall()


def tagValid(tag):
	cursor = conn.cursor()
	if cursor.execute("SELECT * FROM tagged_photos WHERE word = '{0}'".format(tag)):
		return True
	else:
		return False

def getTagQuery(tags):
	query = "SELECT P.imgdata, P.picture_id, P.caption, A.album_title FROM Pictures P, Album A, Tagged_photos T WHERE T.picture_id = P.picture_id AND P.album_id = A.album_id AND T.word = '{0}'".format(tags[0])
	for i in range(1, len(tags)):
		query += " AND P.picture_id IN (SELECT P.picture_id  FROM Pictures P, Album A, Tagged_photos T WHERE T.picture_id = P.picture_id AND P.album_id = A.album_id AND T.word = '{0}')".format(tags[i])
	print(query)
	return query


def getAllTaggedPhotos(tags):
	cursor = conn.cursor()
	if len(tags) == 1:
		return getTaggedPhotos(tags[0])
	else:
		pics = getTaggedPhotos(tags[0])
		for i in pics:
			cursor.execute(getTagQuery(tags))
		return cursor.fetchall()


def getMostCommonTags():
	cursor = conn.cursor()
	cursor.execute("SELECT word, COUNT(word) FROM Tagged_photos GROUP BY word ORDER BY COUNT(word) DESC LIMIT 5")
	return cursor.fetchall()


def findTopUsers():
	cursor = conn.cursor()
	## Pictures count
	pictures_query = "SELECT user_id, count(picture_id) AS count FROM Pictures GROUP BY user_id"
	## Comments count
	comments_query = "SELECT user_id, count(comment_id) AS count FROM Comment WHERE user_id != -1 GROUP BY user_id"
	## sum  
	sum_query = "SELECT U.first_name, U.last_name FROM Users U, (SELECT user_id, SUM(count) as count FROM (" + pictures_query + " UNION " + comments_query + " ) AS Temp WHERE user_id != -1 GROUP BY user_id) AS user_id_counts WHERE U.user_id = user_id_counts.user_id ORDER BY user_id_counts.count DESC LIMIT 10"
	cursor.execute(sum_query)
	print(sum_query)
	return cursor.fetchall()


@app.route("/you_may_also_like")
@flask_login.login_required
def youMayLike():
	uid = getUserIdFromEmail(flask_login.current_user.id)
	pix_with_tags_and_comments = []
	pics = getYouMayAlsoLike(uid)
	for i in pics: 
		pix_with_tags_and_comments += [getTagsAndComments(i)]
	return render_template("show_all_photos.html", message="You may also like", photos=pix_with_tags_and_comments)


def getYouMayAlsoLike(uid):
	cursor = conn.cursor()
	common_tags = getCommonTags(uid)
	lst = []
	for i in common_tags:
		lst += [i[0]]
	pics = commonTagsPhotoSearch(lst, uid)
	return pics

def getCommonTags(uid):
	cursor = conn.cursor()
	cursor.execute("SELECT T.word, Count(T.picture_id) FROM Tagged_photos T, Pictures P WHERE P.picture_id = T.picture_id AND P.user_id = '{0}' GROUP BY word ORDER BY Count(T.picture_id) DESC LIMIT 5".format(uid))
	return cursor.fetchall()

def commonTagsPhotoSearch(tags, uid):
	cursor = conn.cursor()
	query = "SELECT Tags.picture_id, Count(Tags.picture_id) as Pcount FROM ("
	for i in tags:
		query += "SELECT P.picture_id, T.word, P.user_id FROM Pictures P, Tagged_photos T WHERE T.picture_id = P.picture_id AND T.word = '{0}'".format(i)
		query += " UNION "
	query = query[:-7] +  ") as Tags WHERE Tags.user_id != '{0}' GROUP BY Tags.picture_id ORDER BY Pcount DESC".format(uid)
	cursor.execute(query)
	suggested_photos_id = cursor.fetchall()
	suggested_photos = []
	for i in suggested_photos_id:
		suggested_photos += getPhotoFromPhotoId(i[0])
	return suggested_photos

def getPhotoFromPhotoId(picture_id):
	cursor = conn.cursor()
	cursor.execute("SELECT P.imgdata, P.picture_id, P.caption, A.album_title FROM Pictures P, Album A WHERE P.album_id = A.album_id and P.picture_id = '{0}'".format(picture_id))
	return cursor.fetchall()

@app.route("/recommend_tags", methods=["GET", "POST"])
@flask_login.login_required
def recommend():
	uid = getUserIdFromEmail(flask_login.current_user.id)
	if request.method == "POST":
		tags = request.form.get("recommend_tags").split(" ")

		recommended_tags = getRecommendedTags(tags, uid)

		return render_template("profile.html", tags=recommended_tags)
	else:
		return render_template("profile.html", message="Sorry, try again")


def getRecommendedTags(tags, uid):
	cursor = conn.cursor()

	query = "SELECT T.word, Count(T.word) as tcount FROM Tagged_photos T, ("

	for i in tags:
		query += "SELECT P.picture_id, T.word FROM Pictures P, Album A, Tagged_photos T WHERE T.picture_id = P.picture_id AND P.album_id = A.album_id AND T.word = '{0}'".format(i)
		query += " UNION "

	query = query[:-7] +  ") as Tags WHERE Tags.picture_id = T.picture_id"
	for i in tags:
		query += " AND T.word != '{0}'".format(i)
	query += "GROUP BY T.word ORDER BY tcount DESC"
	cursor.execute(query)
	return cursor.fetchall()

#default page  
@app.route("/", methods=['GET'])
def hello():
	return render_template('hello.html', message='Welcome to Photoshare', users=findTopUsers())


if __name__ == "__main__":
	#this is invoked when in the shell  you run 
	#$ python app.py 
	app.run(port=5000, debug=True)
