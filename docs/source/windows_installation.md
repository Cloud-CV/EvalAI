## Installation Instructions for Windows

Setting up EvalAI on your local machine is really easy.
Follow this guide to setup your development machine.

1. Install [python] 2.x (EvalAI only supports python2.x for now.), [git], [postgresql] version >= 9.4, [RabbitMQ] and [virtualenv], in your computer, if you don't have it already.
*If you are having trouble with postgresql on Windows check this link [postgresqlhelp].*

2. Get the source code on your machine via git.

    ```shell
    git clone https://github.com/Cloud-CV/EvalAI.git evalai
    ```

3. Create a python virtual environment and install python dependencies.

    ```shell
    cd evalai
    virtualenv venv
    cd venv/Scripts
    activate.bat    # run this command everytime before working on project
    Then cd to the main evalai folder
    pip install -r requirements/dev.txt
    ```

4. Rename `settings/dev.sample.py` as `dev.py` and change credential in `settings/dev.py`

    ```
    cp settings/dev.sample.py settings/dev.py
    ```
    Use your postgres username and password for fields `USER` and `PASSWORD` in `dev.py` file. 

5. Create an empty postgres database and run database migration.
    Make sure you have defined the PostgreSql path to the Environment Variables.
    
    ```
    createdb evalai
    ```
    Enter your password for authentication and a new database will be added.
    ```
    python manage.py migrate
    ```

6. Seed the database with some fake data to work with.

    ```
    python manage.py seed
    ```
    This command also creates a `superuser(admin)`, a `host user` and a `participant user` with following credentials.

    **SUPERUSER-** username: `admin` password: `password`  
    **HOST USER-** username: `host` password: `password`  
    **PARTICIPANT USER-** username: `participant` password: `password`    

7. That's it. Now you can run development server at [http://127.0.0.1:8000] (for serving backend)

    ```
    python manage.py runserver
    ```


8. Open a new cmd window with node(6.9.2) and ruby(gem) installed on your machine and type

    ```
    npm install
    ``` 
    Install bower(1.8.0) globally by running:
    ```
    npm install -g bower
    ```
    Now install the bower dependencies by running:
    ```
    bower install
    ```
    If you running npm install behind a proxy server, use
    ```
    npm config set proxy http://proxy:port
    ```
9. Now to connect to dev server at [http://127.0.0.1:8888] (for serving frontend)

    ```
    gulp dev:runserver
    ```

10. That's it, Open web browser and hit the url [http://127.0.0.1:8888].
