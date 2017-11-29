## Architecture

EvalAI helps researchers, students, and data scientists to create, collaborate and participate in various AI challenges organized around the world. To achieve this, we leverage some of the best open source tools and technologies.

Technologies that we use

### Django

Django is the heart of the application, which powers our backend. We use Django version 1.10.

### Django Rest Framework

Another awesome framework like Django. We use this to write and provide rest APIs. DRF's permission and serializers have really helped us a lot in writing a maintainable codebase.

### RabbitMQ

We currently use RabbitMQ to queue submission messages, which will then be processed by a Python worker.

### PostgreSQL

PostgresSQL is used as our primary datastore. All our tables currently reside in a single database named `evalai`

### Angular JS

A very well known framework, which beautifully powers our frontend.
