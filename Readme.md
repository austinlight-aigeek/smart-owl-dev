## Smart-Owl for local development

## Setup local environment for running

- `pyenv local 3.11.3` This command set python version 3.11.3 only for the project
- `python --version` Check if `python 3.11.3` is set for the project
- `pip install -r requirements.txt` Will install all required libraries from `requirements.txt`
- `docker-compose -f run_locally/docker-compose.dev.yml up --build`
  - `--build` flag ensures that Docker will rebuild the images specified in the Dockerfile if they are out of date or if there have been any changes to the Dockerfile or the files it copies into the container.
  - Docker will first build the application image by following the steps in the `Dockerfile`.
  - `nginx.conf` file should be in `run_locally` folder to run nginx
- `docker-compose -f run_locally/docker-compose.dbs.yml up -d` `-f` flag specifies the path to the Docker Compose YAML file, `-d`: This flag runs the containers in detached mode, meaning the command will run in the background
- `alembic upgrade head` upgrade your database schema to the latest version as defined by your migration scripts. `alembic.ini` should exist
- `aws dynamodb list-tables --endpoint-url http://localhost:8000 --profile local` will list all tables in dynamodb

Two options to run Smart Owl

- `RUN_LOCALLY=true uvicorn app.main:app --host "localhost" --port 8080 --reload`
- `docker-compose -f run_locally/docker-compose.dev.yml up --build --scale api=2`
