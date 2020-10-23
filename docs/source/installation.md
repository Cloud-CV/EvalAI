# Installation

## Dependencies

[EvalAI] can run on Linux, Cloud, Windows, and macOS platforms. Please install [docker] and [docker-compose] before getting started with the installation of EvalAI.

## Installation instructions

Once you have installed [docker] and [docker-compose], please follow these steps to setup [EvalAI] on your local machine.

1. Get the source code on to your machine via git

   ```shell
   git clone https://github.com/Cloud-CV/EvalAI.git evalai && cd "$_"
   ```

2. Build and run the Docker containers. This might take a while.

   ```
   docker-compose up --build
   ```

3. That's it. Open web browser and hit the URL [http://127.0.0.1:8888](http://127.0.0.1:8888). Three users will be created by default which are listed below:

| User type   | Username    | Password   | Permissions                                                                            |
| ----------- | ----------- | ---------- | -------------------------------------------------------------------------------------- |
| Superuser   | admin       | `password` | Perform CRUD operations on all tables in the database<br /> through django admin panel |
| Host        | host        | `password` | Create and manage challenges                                                           |
| Participant | participant | `password` | Participate in different challenges and make submissions                               |

If you are facing any issue during installation, please see our [common errors during installation page](https://evalai.readthedocs.io/en/latest/faq(developers).html#common-errors-during-installation).

[evalai-cli]: https://cli.eval.ai/
[evalai]: http://eval.ai
[docker-compose]: https://docs.docker.com/compose/install/
[docker]: https://docs.docker.com/install/linux/docker-ce/ubuntu/
