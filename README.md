# CineGuru
#### Video Demo:  https://youtu.be/qET2LxIOAdY
#### Description:
CineGuru is a movie database web application where you can search for movies, write reviews, add to your watchlist and more.

The files used in building this application are as follows:

**application.py**: This is where the program executes. Several routes are created using Flask and each route is assigned a paticular function (such as displaying the webpage when that route is accessed using GET, executing SQL queries, etc.). SQL queries are used which manipulate the given database (such as inserting/deleting a row, accessing rows in a table, etc.). GET and POST requests determine which type of action is to be performed at that particular moment in the given route.

**helpers.py**: This file contains helpful functions that are used in application.py and it makes the application more user friendly (such as displaying error messages in a stylistic fashion, displaying numeric values properly, etc.).

**movies.db**: This is the database file where information about movies, directors, cast members and users are stored. These values are accessed using SQL in application.py.

**mov_info.csv**: This file contains real-time information about a movie when a user searches it. This information can be used for database querying using SQL. The previous data gets replaced when a user searches for another movie.

**requirements.txt**: This file contains library names that can be installed using the 'pip' command.

**script.js**: This file contains code that makes the navbar static while scrolling a webpage.

**styles.css**: This file is used for styling content of the html pages.

Code generating the homepage (i.e., the webpage on accessing the / route) is written in index.html. Likewise, code generating the login page is written in login.html, and so on.

First, you need to register for an account by clicking on the 'Register' button on the navbar. After you register, you may log in. You can also change your password if you want, by clicking on the "Change Password" button.

You will be able to access the homepage after a successful log in. Here you can search for a movie by typing its name in the search field and clicking on the 'Search' button. You can (optionally) specify the year of release in order to resolve conflicts when multiple movies have the same title.

Once you click on 'Search', you will be able to see the general information about the movie (located in the 'General' tab on the navbar). If the movie is not found, you will receive an apology. The 'Cast' tab (located on the navbar) will show you the leading stars and directors of the movie, and the 'Reviews' tab is where you can write movie reviews. Your review can be read by anyone after you submit it.

The page in the 'General' tab has three buttons; "Watch trailer", "Watched" and "Add to Watchlist". Clicking on "Watch Trailer" will redirect to YouTube, with the search query automatically inserted to show only the trailers for the movie. Clicking on "Watched" and "Add to Watchlist" will add the movie to your "Watched Movies" list and your watchlist respectively, where you can refer to it later (these can be accessed from buttons on the navbar).

You can even add a movie that is not present in the database. Simply click on the "Add a Movie" button present on the navbar, input the relevant information and then click on "Add to Database". The movie will be added.
