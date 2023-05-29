# IdeaHub
IdeaHub is a social media platform built using Flask, Jinja, SQLite, HTML, and Bootstrap. The platform allows users to create profiles, share posts, and interact with others through likes.

A more detailed description of what IdeaHub could be can be found in [info.txt](info.txt)

## Requirements
Python, which can be downloaded at this [link](https://www.python.org/downloads/) is required to run this application. All the modules required to run the application are included in the file [requirements.txt](https://github.com/Suhana66/IdeaHub/blob/master/requirements.txt). A virtual environment to run the application can be created using the following commands in the command line.

```
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Inside the virtual environment, the application can be run using the command `flask run`.

## Features
IdeaHub includes the following features:
* User registration and login
* Post creation, deletion and drafting
* Post liking
* Search functionality

## Code Structure
* app.py: the main Flask application file
* schema.sql: SQL statements to create necessary tables for the application
* templates/: Jinja templates for the views
* static/: static files for the application, JavaScript files and GIFs

## License
The GIFs used in this application are in the public domain and can be found at the following links, [disney-aristocats.gif](http://gifgifs.com/creatures-cartoons/cartoon-characters/35107-disney-aristocats.html) and [batman-says-no.gif](http://gifgifs.com/creatures-cartoons/cartoon-characters/35099-batman-says-no.html).

All other files in this project is licensed under the GNU GPLv3 License - see the [LICENSE](COPYING) file for details.
