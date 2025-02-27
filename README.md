
# Deployer

This project can be used inside a CICD pipeline to execute deployments and undeployments of applications in a broker mesh.

## Prerequisites

- python3 [> 3.10]
- virtual environment activated
- 
```console
 python -m venv .venv
 source .venv/bin/activate
```

By running the following command, all dependencies will be installed/updated according to the content of the pyproject.toml file.
```console
python -m pip install -e . 
```

```console
$ deploy --conf=[location of the configuration json file] [--action=[deploy/undeploy] --appl=[name(s) of the application(s) to execute the action for]
``
