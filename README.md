
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

## Running the deployer

When you want to run the deployer you need to prepare a json file with a given configuration.

Check the json files in the folder `config`. This holds the base uri for the CloudAPI together with an API token that has sufficient rights to execute deployments.
There is an array with applications for the given applicationDomain and the versions that need to be installed on the environment.
There are checks built in to prevent installation of Draft applications in environments other than `Dev`.

```json
{
  "baseUrl": "https://api.solace.cloud/api/v2",
  "token":  "eyJhbGciOiJSUzI1NiIsImtpZCI6Im1hYXNfcHJvZF8yMDIwMDMyNiIsInR5cCI6IkpXVCJ9.eyJvcmciOiJzb2xhY2V1c2VycyIsIm9yZ1R5cGUiOiJFTlRFUlBSSVNFIiwic3ViIjoieWFlamRpYWZxMjYiLCJwZXJtaXNzaW9ucyI6IkFBQUFBSUF2QUFBQWZ6Z0E0QUVBQUFBQUFBQUFBQUFBQUlDeHpvY2hJQWpnTC8vL2c1WGZCZDREV01NRDQ0ZTVNNE1aRVA1L0JnRElJZz09IiwiYXBpVG9rZW5JZCI6ImloanE3dmt1NXZqIiwiaXNzIjoiU29sYWNlIENvcnBvcmF0aW9uIiwiaWF0IjoxNzM4NzUwMjY4fQ.B44WH_E_xkrj4P4gNOHuY3cy7p-STv1fGkVHmA_yMvmidED2_M0kvI0fZ5qc8UqZp-NU9PXI60fPpKhFF8oNHX2LecaFwIax6qtx75x3Buzn7qpwmE2zycnvfgsWyX1QaXr-jyBSrMjUkxQzbgTLPue1h9VytfU05_tPrpUnL_5BgrWZ2LvsRmON1XG5wu2X_RLEL8_8lZZX5XRxf8MJX3EZfDERce3eTaaTAnwQ6oLMks-XUTxg0uDnFdfVC8Ti2bKpnJY6yWMOk7E1R4i38yw8OyS5hyH9ViLKKYkCm_XXJ_b2tDZ80AtEQKYdkhJQ0avm5lHyNNKuJBL_v6c9Sw",
  "environment": "dev",
  "environmentName": "Dev",
  "memName": "Enexis-MEM",
  "domainName": "EXS-Chauffeurs",
  "applications": [
    {
      "name": "MENDIX",
      "version": "0.1.1"
    },
    {
      "name": "SAP26",
      "version": "0.1.0"
    }
  ]
}
```

Example of deploy action for MENDIX application
```console
$ deploy --conf=[location of the configuration json file] --action=deploy --appl=MENDIX
```
Leave out the `--appl=[...]` part for deployment of all applications.

Example of undeploy action for SAP26 application
```console
$ deploy --conf=[location of the configuration json file] --action=undeploy --appl=SAP26
```
Leave out the `--appl=[...]` part for undeployment of all applications.
