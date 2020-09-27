## Deploying EvalAI on VM

Deploying EvalAI on-prem is now easier using the deployment script. Things like setting up SSL certs with certbot, automatic local database backup have been added to make things easier on the organizer's end. This version of the deployment script spins up a dev version of EvalAI, to use EvalAI prod version with the AWS workers, see the next guide.

### 1. Getting the VM instance and routing ready

Since this version of the script should be cloud platform agnostic, set up an Ubuntu VM instance and set the traffic to route to the IP address of VM instance.


### 2. Clone and checkout the deployment branch

Now that you have got the instance ready, simply SSH into your instance. Then, clone the project and check out the deployment script branch.

```
git clone https://github.com/Cloud-CV/EvalAI.git && cd EvalAI
git fetch origin pull/2853/head:v1_deploy
git checkout v1_deploy
```

### 3. Run the deployment script

To run the deployment script, run the following command : 

```
./scripts/ec2_deployment/deploy.sh
```

Then, input the fields and you're done !


### Database backup/restore commands

The postgres database is automatically backed up by a separate container every 24 hours (which can be configured in docker-compose file). 

To manually backup the database (replace pgbackups_container_name):
```
sudo docker exec -it $pgbackups_container_name /backup.sh -e POSTGRES_HOST=postgres -e POSTGRES_DB=db -e POSTGRES_USER=postgres -e POSTGRES_PASSWORD=postgres
```

To manually restore the database (replace pgbackups_container_name):
```
sudo docker exec -it $pgbackups_container_name gunzip -c $backup_path | psql -h db -p 5432 -U postgres -d postgres
```
