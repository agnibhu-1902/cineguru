import os
import csv
import time

from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError
from werkzeug.security import check_password_hash, generate_password_hash
from datetime import datetime

from helpers import apology, login_required, usd

# Configure application
app = Flask(__name__)

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True


# Ensure responses aren't cached
@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


# Custom filter
app.jinja_env.filters["usd"] = usd

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///movies.db")



@app.route("/", methods=["GET", "POST"])
@login_required
def index():
    if request.method == "POST":
        return redirect("/search")
    else:
        return render_template("index.html")


@app.route("/search", methods=["GET", "POST"])
@login_required
def search():
    if request.method == "POST":
        if "watched" in request.form:
            # Add movie to "Watched Movies" List
            with open("mov_info.csv") as file:
                reader = csv.DictReader(file)
                for row in reader:
                    movies = db.execute("SELECT * FROM watched WHERE title = ? AND id = ?", row["title"], session["user_id"])
                    if len(movies) == 0:
                        db.execute("INSERT INTO watched (id, title, year) VALUES(?, ?, ?)", session["user_id"], row["title"], row["year"])
                        flash(f"{row['title']} has been successfully added to your \"Watched Movies\" list")
                    else:
                        flash(f"{row['title']} is already present in your \"Watched Movies\" list")
                    movies = db.execute("SELECT * FROM watchlist WHERE title = ? AND id = ?", row["title"], session["user_id"])
                    if len(movies) != 0:
                        db.execute("DELETE FROM watchlist WHERE title = ? AND year = ?", row["title"], row["year"]) # Delete from watchlist
        elif "watchlist" in request.form:
            # Add movie to watchlist
            with open("mov_info.csv") as file:
                reader = csv.DictReader(file)
                for row in reader:
                    movies = db.execute("SELECT * FROM watchlist WHERE title = ? AND id = ?", row["title"], session["user_id"])
                    if len(movies) == 0:
                        db.execute("INSERT INTO watchlist (id, title, year) VALUES(?, ?, ?)", session["user_id"], row["title"], row["year"])
                        flash(f"{row['title']} has been successfully added to your watchlist")
                    else:
                        flash(f"{row['title']} is already present in your watchlist")
                    movies = db.execute("SELECT * FROM watched WHERE title = ? AND id = ?", row["title"], session["user_id"])
                    if len(movies) != 0:
                        db.execute("DELETE FROM watched WHERE title = ? AND year = ?", row["title"], row["year"]) # Delete from "Watched Movies" list
        elif "trailer" in request.form:
            with open("mov_info.csv") as file:
                reader = csv.DictReader(file)
                s=''
                for row in reader:
                    words = row["title"].lower().split(' ')
                    for i in range(len(words) - 1):
                        s += words[i] + '+'
                    s += words[-1]
                    return redirect(f"https://www.youtube.com/results?search_query={s}+{row['year']}+trailer") # Send a get request to YouTube
        else:
            # Search for the movie in the database
            if request.form.get("year") == "":
                movies = db.execute("SELECT * FROM movies WHERE title LIKE ?", request.form.get("search"))
            else:
                movies = db.execute("SELECT * FROM movies WHERE title LIKE ? AND year = ?", request.form.get("search"), request.form.get("year"))
            if len(movies) == 0:
                return apology("movie not found", 404) # When movie is not present in the database
            mov_id, title, year = movies[0]["id"], movies[0]["title"], movies[0]["year"]
            rating = db.execute("SELECT rating, votes FROM ratings WHERE movie_id = ?", mov_id)
            persons = db.execute("SELECT person_id FROM directors WHERE movie_id = ?", mov_id)
            directors=[]
            for person in persons:
                name = db.execute("SELECT name FROM people WHERE id = ?", person["person_id"])
                directors.append(name[0]["name"])
            with open("mov_info.csv", "w") as file:
                header = csv.DictWriter(file, fieldnames=["title", "year", "rating", "vote", "directors"])
                header.writeheader()
                writer = csv.writer(file)
                writer.writerow([title, year, rating[0]["rating"], rating[0]["votes"], directors])
            if "watched" in request.form:
                db.execute("INSERT INTO watched (id, title) VALUES(?, ?)", session["user_id"], title)
            elif "watchlist" in request.form:
                db.execute("INSERT INTO watchlist (id, title) VALUES(?, ?)", session["user_id"], title)
        return redirect("/search", code=303)
    else:
        with open("mov_info.csv") as file:
            reader = csv.DictReader(file)
            for row in reader:
                return render_template("result.html", title=row["title"], year=row["year"], rating=row["rating"], vote=int(row["vote"]), directors=row["directors"].replace("'", "").strip('][').split(', '))


@app.route("/cast")
@login_required
def cast():
    # Display the cast of the movie
    with open("mov_info.csv") as file:
        reader = csv.DictReader(file)
        for row in reader:
            mov_id = db.execute("SELECT id FROM movies WHERE title LIKE ? AND year = ?", row["title"], row["year"])
            person_id = db.execute("SELECT person_id FROM stars WHERE movie_id = ?", mov_id[0]["id"])
            stars, s_birth=[], []
            for person in person_id:
                name = db.execute("SELECT name, birth FROM people WHERE id = ?", person["person_id"])
                stars.append(name[0]["name"])
                s_birth.append(name[0]["birth"])
            person_id = db.execute("SELECT person_id FROM directors WHERE movie_id = ?", mov_id[0]["id"])
            directors, d_birth=[], []
            for person in person_id:
                name = db.execute("SELECT name, birth FROM people WHERE id = ?", person["person_id"])
                directors.append(name[0]["name"])
                d_birth.append(name[0]["birth"])
            return render_template("cast.html", title=row["title"], stars=stars, s_birth=s_birth, directors=directors, d_birth=d_birth)


@app.route("/reviews", methods=["GET", "POST"])
@login_required
def reviews():
    # Display the reviews of the movie
    if request.method == "POST":
        if request.form.get("review") == "":
            return apology("Input Field is empty", 403)
        else:
            uname = db.execute("SELECT username FROM users WHERE id = :user_id", user_id=session["user_id"])
            with open("mov_info.csv") as file:
                reader = csv.DictReader(file)
                for row in reader:
                    db.execute("INSERT INTO reviews (id, username, movie, review) VALUES(?, ?, ?, ?)", session["user_id"], uname[0]["username"], row["title"], request.form.get("review"))
                    break
        return redirect("/reviews", code=303)
    else:
        reviews = db.execute("SELECT username, movie, review FROM reviews")
        with open("mov_info.csv") as file:
            reader = csv.DictReader(file)
            for row in reader:
                return render_template("reviews.html", title=row["title"], reviews=reviews)


@app.route("/watched")
@login_required
def watched():
    # Display the "Watched Movies" list
    watched = db.execute("SELECT title, year FROM watched WHERE id = :user_id", user_id=session["user_id"])
    return render_template("watched.html", watched=watched)


@app.route("/watchlist")
@login_required
def watchlist():
    # Display the watchlist
    watchlist = db.execute("SELECT title, year FROM watchlist WHERE id = :user_id", user_id=session["user_id"])
    return render_template("watchlist.html", watchlist=watchlist)


@app.route("/add", methods=["GET", "POST"])
@login_required
def add():
    # Add the movie to the database
    if request.method == "POST":
        flag = False
        year = request.form.get("bdir").split(',')
        for value in year:
            if not value.strip().isdigit():
                if not value.strip() == '':
                    flag = True
                    break
        year = request.form.get("bstar").split(',')
        for value in year:
            if not value.strip().isdigit():
                if not value.strip() == '':
                    flag = True
                    break
        # Check for errors in user input
        if flag:
            return apology("only numbers allowed in year fields", 400)
        elif request.form.get("title") == '' or request.form.get("year") == '' or request.form.get("director") == '' or request.form.get("bdir") == '' or request.form.get("stars") == '' or request.form.get("bstar") == '' or request.form.get("rating") == '' or request.form.get("votes") == '':
            return apology("please fill in all fields", 400)
        elif len(request.form.get("director").split(',')) != len(request.form.get("bdir").split(',')):
            return apology("director name and year fields don't match", 400)
        elif len(request.form.get("stars").split(',')) != len(request.form.get("bstar").split(',')):
            return apology("star name and year fields don't match", 400)
        title, year = request.form.get("title"), request.form.get("year")
        movie = db.execute("SELECT * FROM movies WHERE title LIKE ? and year = ?", title, year)
        if len(movie) != 0:
            flash(f"{title} is already present in the database") # Check if movie is already present in the database
        else:
            # Add to database
            db.execute("INSERT INTO movies (title, year) VALUES(?, ?)", title, year)
            movie = db.execute("SELECT id FROM movies WHERE title = ? AND year = ?", title, year)
            db.execute("INSERT INTO ratings (movie_id, rating, votes) VALUES(?, ?, ?)", movie[0]["id"], request.form.get("rating"), request.form.get("votes"))
            if ',' in request.form.get("director"):
                director = request.form.get("director").split(',')
                year = request.form.get("bdir").split(',')
                for i in range(len(director)):
                    search = db.execute("SELECT * FROM people WHERE name LIKE ? AND birth = ?", director[i].strip(), year[i].strip())
                    if len(search) != 0:
                        db.execute("INSERT INTO directors (movie_id, person_id) VALUES(?, ?)", movie[0]["id"], search[0]["id"])
                    else:
                        db.execute("INSERT INTO people (name, birth) VALUES(?, ?)", director[i].strip(), year[i].strip())
                        search = db.execute("SELECT id FROM people WHERE name LIKE ? AND birth = ?", director[i].strip(), year[i].strip())
                        db.execute("INSERT INTO directors (movie_id, person_id) VALUES(?, ?)", movie[0]["id"], search[0]["id"])
            else:
                director, bdir = request.form.get("director").strip(), request.form.get("bdir").strip()
                search = db.execute("SELECT * FROM people WHERE name LIKE ? AND birth = ?", director, bdir)
                if len(search) != 0:
                    db.execute("INSERT INTO directors (movie_id, person_id) VALUES(?, ?)", movie[0]["id"], search[0]["id"])
                else:
                    db.execute("INSERT INTO people (name, birth) VALUES(?, ?)", director, bdir)
                    search = db.execute("SELECT id FROM people WHERE name LIKE ? AND birth = ?", director, bdir)
                    db.execute("INSERT INTO directors (movie_id, person_id) VALUES(?, ?)", movie[0]["id"], search[0]["id"])
            if ',' in request.form.get("stars"):
                stars = request.form.get("stars").split(',')
                year = request.form.get("bstar").split(',')
                print(stars)
                print(year)
                for i in range(len(stars)):
                    search = db.execute("SELECT * FROM people WHERE name LIKE ? AND birth = ?", stars[i].strip(), year[i].strip())
                    if len(search) != 0:
                        db.execute("INSERT INTO stars (movie_id, person_id) VALUES(?, ?)", movie[0]["id"], search[0]["id"])
                    else:
                        db.execute("INSERT INTO people (name, birth) VALUES(?, ?)", stars[i].strip(), year[i].strip())
                        search = db.execute("SELECT id FROM people WHERE name LIKE ? AND birth = ?", stars[i].strip(), year[i].strip())
                        db.execute("INSERT INTO stars (movie_id, person_id) VALUES(?, ?)", movie[0]["id"], search[0]["id"])
            else:
                star, bstar = request.form.get("stars").strip(), request.form.get("bstar").strip()
                search = db.execute("SELECT * FROM people WHERE name LIKE ? AND birth = ?", star, bstar)
                if len(search) != 0:
                    db.execute("INSERT INTO stars (movie_id, person_id) VALUES(?, ?)", movie[0]["id"], search[0]["id"])
                else:
                    db.execute("INSERT INTO people (name, birth) VALUES(?, ?)", star, bstar)
                    search = db.execute("SELECT id FROM people WHERE name LIKE ? AND birth = ?", star, bstar)
                    db.execute("INSERT INTO stars (movie_id, person_id) VALUES(?, ?)", movie[0]["id"], search[0]["id"])
            flash(f"{title} has been successfully added to the database")
        return redirect("/add", code=303)
    else:
        return render_template("add.html")


@app.route("/password", methods=["GET", "POST"])
def password():
    """Change password"""

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username", 400)

        # Ensure password was submitted
        elif not request.form.get("old_password"):
            return apology("must provide password", 400)

        # Ensure password was submitted
        elif not request.form.get("new_password"):
            return apology("must provide password", 400)

        # Ensure password was submitted
        elif not request.form.get("confirmation"):
            return apology("must provide password", 400)

        # Query database for username
        rows = db.execute("SELECT * FROM users WHERE username = ?", request.form.get("username"))

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], request.form.get("old_password")):
            return apology("invalid username and/or password", 400)

        # Ensure passwords match
        elif request.form.get("new_password") != request.form.get("confirmation"):
            return apology("passwords don't match", 400)

        # Change user's password
        username = request.form.get("username")
        password = request.form.get("new_password")
        db.execute("UPDATE users SET hash = ? WHERE username = ?", generate_password_hash(password), username)

        # Redirect user to login page
        return redirect("/login")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("password.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username", 403)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 403)

        # Query database for username
        rows = db.execute("SELECT * FROM users WHERE username = ?", request.form.get("username"))

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], request.form.get("password")):
            return apology("invalid username and/or password", 403)

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")


@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")


@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username", 400)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 400)

        # Ensure passwords match
        elif request.form.get("password") != request.form.get("confirmation"):
            return apology("passwords don't match", 400)

        # Ensure username is not taken
        else:
            rows = db.execute("SELECT * FROM users WHERE username = ?", request.form.get("username"))
            if len(rows) != 0:
                return apology("username already taken", 400)

        # Add user to database
        username = request.form.get("username")
        password = request.form.get("password")
        db.execute("INSERT INTO users (username, hash) VALUES(?, ?)", username, generate_password_hash(password))

        # Redirect user to login page
        return redirect("/login")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("register.html")


def errorhandler(e):
    """Handle error"""
    if not isinstance(e, HTTPException):
        e = InternalServerError()
    return apology(e.name, e.code)


# Listen for errors
for code in default_exceptions:
    app.errorhandler(code)(errorhandler)

if __name__ == "__main__":
    app.run(debug = False, host = '0.0.0.0')
