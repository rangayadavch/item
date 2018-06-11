# Item Catalog Project 
This is my fourth project in Udacity Fullstack nanodegree course.

## About
This project is a RESTful web application utilizing the Flask framework which accesses a SQL database that populates categories and their items. OAuth2 provides authentication for further CRUD functionality on the application. Currently OAuth2 is implemented for Google Accounts.

## In This Repo
This project has one main Python module app.py which runs the Flask application. A SQL database is created using the database_setup.py module and you can populate the database with test data using database_init.py. The Flask application uses stored HTML templates in the tempaltes folder to build the front-end of the application. CSS/JS/Images are stored in the static directory.

## Skills Required
1.Python
2.HTML
3.CSS
4.OAuth
5.Flask Framework

## Dependencies
Vagrant 
Udacity Vagrantfile 
VirtualBox 
## How to Install 
Install Vagrant & VirtualBox 
Clone the Udacity Vagrantfile 
Go to Vagrant directory and either clone this repo or download and place zip here 
Launch the Vagrant VM (vagrant up)
Log into Vagrant VM (vagrant ssh)
Navigate to cd/vagrant as instructed in terminal
The app imports requests which is not on this vm. Run sudo pip install requests
Setup application database python /item-catalog/database_setup.py
*Insert fake data python /item-catalog/database_init.py
Run application using python /item-catalog/app.py
Access the application locally using http://localhost:5000
