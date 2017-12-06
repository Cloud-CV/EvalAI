## Architecture

EvalAI helps researchers, students, and data scientists to create, collaborate, and participate in various AI challenges organized around the globe. To achieve this, we leverage some of the best open source tools and technologies available.

### Technologies that the project use:

#### Django

Django is the heart of the application. It powers our complete backend. We use Django version 1.10.

#### Django Rest Framework

We use Django Rest Framework for writing and providing REST APIs. Its permission and serializers have helped write a maintainable codebase.

#### RabbitMQ

We currently use RabbitMQ for queueing submission messages which are then later on processed by a Python worker.

#### PostgreSQL

PostgreSQL is used as our primary datastore. All our tables currently reside in a single database named as `evalai`.

#### Angular JS

A well-known framework that powers our frontend.
