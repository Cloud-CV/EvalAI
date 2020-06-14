# EvalAI-ngx

Revamped codebase of EvalAI Frontend

### For deploying with [Surge](https://surge.sh/):

Surge will automatically generate deployment link whenever a pull request passes Travis CI. 

Suppose pull request number is 123 and it passes Travis CI. The deployment link can be found here: `https://pr-123-evalai.surge.sh`

## Code scaffolding

Run `ng generate component component-name` to generate a new component. You can also use `ng generate directive|pipe|service|class|guard|interface|enum|module`.

## Code Documentation

We are using [compodoc](https://compodoc.github.io/website/guides/jsdoc-tags.html) for documentation. The goal of this tool is to generate a documentation for all the common APIs of the application like modules, components, injectables, routes, directives, pipes and classical classes.

Compodoc supports [these](https://compodoc.github.io/website/guides/jsdoc-tags.html) JSDoc tags.

### Building and Serving the documentation

Run the following command to build and serve the docs:
```
npm run doc:buildandserve
```
Open http://localhost:8080 in the browser to have a look at the generated docs.

## Build

Run `ng build` to build the project. The build artifacts will be stored in the `dist/` directory. Use the `-prod` flag for a production build.

## Running unit tests

Run `ng test` to execute the unit tests via [Karma](https://karma-runner.github.io).

## Running end-to-end tests

Run `ng e2e` to execute the end-to-end tests via [Protractor](http://www.protractortest.org/).
