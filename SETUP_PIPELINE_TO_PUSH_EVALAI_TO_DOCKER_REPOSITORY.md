## Setup Pipeline to push EvalAI to Docker Repository

In order to setup pipeline to push EvalAI to Docker Repository we have to do the following:

### Push Docker Image to a Registry

To push an image to a Docker registry, you have to authenticate via docker login first. The authentication details (username, email and password) used for login should be stored in the repository settings environment variables. This may be set up through the repository settings web page or locally via the Travis CLI like so:

```
travis env set DOCKER_USERNAME evalai_username
travis env set DOCKER_PASSWORD secret_evalai password
```

Within your `.travis.yml` before attempting a `docker push` or perhaps before `docker pull` of a private image like so:

```
echo "$DOCKER_PASSWORD" | docker login -u "$DOCKER_USERNAME" --password-stdin
```

### Branch Based Registry Pushes

To push a particular branch of your repository to a remote registry, use the custom deploy section of your `.travis.yml`:

Add the following:

```
deploy:
  provider: script
  script: bash docker_push
  on:
    branch: master
```

Where `docker_push` is a script in your repository containing:

```
#!/bin/bash
echo "$DOCKER_PASSWORD" | docker login -u "$DOCKER_USERNAME" --password-stdin
docker push USER/REPO
```

### Private Registry Login

When pushing to a private registry, be sure to specify the hostname in the `docker login` command:

```
echo "$DOCKER_PASSWORD" | docker login -u "$DOCKER_USERNAME" --password-stdin registry.example.com
```

I believe these would suit our use case. We just need to add these codes to their respective files.
