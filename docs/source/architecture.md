## Architecture

EvalAI helps researchers, students, and data-scientists to create, collaborate and participate in various AI challenges organized round the globe. To achieve this we leverage some of the best open source tools and technologies.

Technologies that the project use

### Django

Django is the heart of the application. It powers our complete backend. We use Django version 1.10.

### Django Rest Framework

Another awesome framework like Django, We use Django rest framework for writing and providing rest APIs. DRF's permission and serializers have really helped us a lot in writing maintainable codebase.

### RabbitMQ

We presently use RabbitMQ for queueing submission messages which are then later on processed by a Python worker.

### PostgreSQL

PostgresSQL is used as a primary datastore. All our tables currently reside in a single database named as `evalai`

### Angular JS

A very well known framework, which beautifully powers our frontend.
