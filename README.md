# EvalAI-ngx
Revamped codebase of EvalAI Frontend

## Quick Setup 
```shell
npm install -g @angular/cli
git clone git@github.com:Cloud-CV/EvalAI-ngx.git
cd EvalAI-ngx/
npm install
```

## Development server

Run `ng serve` for a dev server. Navigate to `http://localhost:4200/`. The app will automatically reload if you change any of the source files.

## Code scaffolding

Run `ng generate component component-name` to generate a new component. You can also use `ng generate directive|pipe|service|class|guard|interface|enum|module`.

## Build

Run `ng build` to build the project. The build artifacts will be stored in the `dist/` directory. Use the `-prod` flag for a production build.

## Running unit tests

Run `ng test` to execute the unit tests via [Karma](https://karma-runner.github.io).

## Running end-to-end tests

Run `ng e2e` to execute the end-to-end tests via [Protractor](http://www.protractortest.org/).
### Using Docker

You can also use Docker Compose to run all the components of EvalAI-ngx together. The steps are:

1. Get the source code on to your machine via git.

    ```shell
    git clone https://github.com/Cloud-CV/EvalAI-ngx.git && cd EvalAI-ngx
    ```

2. Build and run the Docker containers. This might take a while. You should be able to access EvalAI at `localhost:8888`.

    ```
    docker-compose -f docker-compose.dev.yml up -d --build
    ```