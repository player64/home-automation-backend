# Home automation - Backend Django
This project aims to develop a user-friendly web application where a user will be able
to manage its devices. Furthermore, by automating various tasks such as enable/disable based on the current
environment state read from the sensors, electrical appliances will help reduce the energy bill, e.g.,
the system will disable a heater if the temperature in the room reaches a certain value. 
This part of the project was designed to create a REST API to communicate with the frontend application 
[Home automation frontend VUE](https://github.com/player64/home-automation-frontend). 
The application implements Json Web Token to authenticate the requests.


### Project setup
Create Python virtual environment. 

To install the project's dependencies, use the below command.

```
pip install -r requirements.txt
```

To create migration files run the command.

```
python manage.py makemigrations
```

To populate the database tables and create a default database SQLite for development purposes. Use the command.

```
python manage.py migrate
```

To create a superuser use the command.

```
python manage.py createsuperuser
```

### Development server 
Before run development server the static files needs to be created by the command.
```
python manage.py collectstatic
```

To run the development server use the command 

```
python manage.py runserver
```

### Background tasks
The project uses the Django Background Tasks to enable device's automation. This feature might not work correctly 
on development environment. The developed tasks are:

* sensor tasks - the tasks runs every hour to save sensors readings
* relay tasks - the task runs every five minutes to execute defined events based on sensors readings.
* time tasks - the task runs every minute to execute time based events. 

To register those task use the command.

```
python manage.py run_devices_task
```

After registering tasks to run them use the command below

```
python manage.py process_tasks
```

### Project test
This project was tested under Python 3.8 and 3.9. To run the tests use the command below.

```
python manage.py test
```