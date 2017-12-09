## Architecture

EvalAI helps researchers, students, and data scientists to create, collaborate and participate in various AI challenges organized around the globe. To achieve this, we leverage some of the best open source tools and technologies.

### Technologies that the project uses:

#### Django

Django is at the heart of the application. It powers our whole backend. We use Django version 1.10.

#### Django Rest Framework

We use the Django Rest Framework for writing and providing REST APIs. Its permissions and serializers have helped us to write a maintainable codebase.

#### RabbitMQ

We currently use RabbitMQ for queueing submission messages which are later processed by a Python worker.

#### PostgreSQL

PostgresSQL is used as our primary datastore. All our tables currently reside in a single database named `evalai`

#### Angular JS

Angular JS is a well-known framework that powers our frontend.
