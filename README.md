# Chaostoolkit-Examples-for-PRECISE

## Prepeare the environment

This guide assumes you use `uv` (https://docs.astral.sh/uv/pip/environments/) as python virtual environment.

### Init environment

```sh
$ cd Chaostoolkit-Examples-for-PRECISE
$ uv venv --python 3.13
```

### Install Dependencies

```sh
$ uv pip install chaostoolkit
$ uv pip install flask
```

Check if chaostoolkit is installed and is working:

```sh
$ chaos --version
chaos, version 1.19.0
```

## Run Your First Experiment

Now execute your chaos experiment following these steps:

**Start the Flask Application**

In terminal 1 (with the virtual environment activated):

```sh
$ uv run python backend/app.py
````

In terminal 2 (with the virtual environment activated):

```sh
$ uv run python frontend/app_v1_bad.py
````

In terminal 3 (with the virtual environment activated):

```sh
$ uv run chaos run experiments/experiment_1_baseline.json
```

## Further experiments

Experiment by running the backend with a delay:

```sh
$ uv run BACKEND_DELAY=2 python backend/app.py
```

.. and switch between the two frontends and running the three experiment files.


