import sys
import json
from enum import Enum

import requests
from jsonpath_ng.ext import parse
import argparse
import logging

class Environment(Enum):
    DEV = 'dev'
    TST = 'tst'
    PRD = 'prd'

class Action(Enum):
    DEPLOY = 'deploy'
    UNDEPLOY = 'undeploy'

def setup_logging(log_level):
    numeric_level = getattr(logging, log_level.upper(), None)
    if not isinstance(numeric_level, int):
        raise ValueError(f"Invalid log level: {log_level}")
    for handler in logging.root.handlers[:]:
        logging.root.removeHandler(handler)

    logging.basicConfig(
        level=numeric_level,
        format="%(asctime)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        handlers=[logging.StreamHandler(sys.stdout)]
    )

def parse_arguments():
    parser = argparse.ArgumentParser(description="Process some parameters")
    parser.add_argument("--conf", type=str, help="location of the config file to use", default="config/dev.json")
    parser.add_argument("--appl", type=str, help="Application Name, one of [MENDIX, SAP26]", default=None)
    parser.add_argument("--action", type=str, help="Action, one of [deploy, undeploy]", default="deploy")
    parser.add_argument("--log", type=str, help="Set the logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL", default="INFO")
    return parser.parse_args()

def load_config(file_path):
    try:
        with open(file_path, "r") as file:
            return json.load(file)
    except FileNotFoundError:
        logging.error(f"Error: Config file '{file_path}' not found.")
        sys.exit(1)
    except json.JSONDecodeError:
        logging.error(f"Error: Invalid JSON format in file '{file_path}'.")
        sys.exit(1)

def get_response(url, headers=None, params=None):
    if headers is None:
        headers = {}
    try:
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status() # Raise and error for bad status codes
        logging.debug(f"url= { response.request.url } ")
        result = response.json()
        return result.get('data', None)
    except requests.exceptions.RequestException as e:
        logging.error(f"Http Request failed: {e}")
        return None
    except ValueError:
        logging.error("Failed to parse JSON.")
        return None

def filter_response(data, property_name=None, filter_key=None, filter_value=None, path_expr=None):
    if path_expr:
        logging.debug(f"path_expr = { path_expr }")
        jsonpath_expr = parse(path_expr)
        return [match.value for match in jsonpath_expr.find(data)]
    if isinstance(data, list): # if the response is a list
        filtered_items = [item for item in data if isinstance(item, dict) and item.get(filter_key) == filter_value]
        return filtered_items[0][property_name] if filtered_items else None
    elif isinstance(data,dict): # if the response is a dictionary
        if property_name in data:
            value = data[property_name]
            if isinstance(value, list) and filter_key and filter_value:
                filtered_items = [item for item in value if isinstance(item,dict) and item.get(filter_key) == filter_value]
                return filtered_items[0][property_name] if filtered_items else None
            return value
        else :
            return None

def fetch_property(url, headers=None, params=None, property_name=None, key=None, value=None, path_expr=None):
    data = get_response(url, headers, params)
    return filter_response(data, property_name, key, value, path_expr) if data else None

def execute_action(url, headers, action, application, version_id, broker_id):
    if headers is None:
        headers = {}
    payload = {
        "applicationVersionId": version_id,
        "action": action,
        "eventBrokerId": broker_id
    }
    logging.debug(f"payload= {payload}")
    response = requests.post(url, headers=headers, json=payload)
    if response.status_code == 200:
        logging.info(f"Action { action } of application { application['name'] } version { application['version'] }, id { version_id } successful on broker { broker_id }")
        logging.debug(f"Response JSON: { response.json() }\n")
    else:
        logging.error(f"Action { action } of application { application['name'] } version { application['version'] }, id { version_id } failed on broker { broker_id }")
        logging.error(f"Status: { response.status_code }\n")
        logging.error( response.text )

def is_version_eligible(env, action, version):
    logging.info(f"Check if application version is eligible for the given environment")
    # if env == dev and version.state in [1, 2] and action == 'deploy' => True
    # if env == dev and action == 'undeploy' => True
    # if env in [tst, prd] and version.state == 2 and action == 'deploy' => True
    # if env in [tst, prd] and version.state in [2, 3, 4] and action == 'undeploy' => True
    # else False
    if ((env == Environment.DEV.value and version.get('stateId') in ['1','2'] and action == Action.DEPLOY.value) or
            (env == Environment.DEV.value and action == Action.UNDEPLOY.value)):
        return True
    if ((env in [Environment.TST.value, Environment.PRD.value] and version.get('stateId') == '2' and action == Action.DEPLOY.value) or
            (env in [Environment.TST.value, Environment.PRD.value] and version.get('stateId') in ['2','3','4'] and action == Action.UNDEPLOY.value)):
        return True
    return False

SNAKE = r"""  \
   \    ___
    \  (o o)
        \_/ \
         λ \ \
           _\ \_
          (_____)_
         (________)=Oo°
"""


def bubble(message):
    bubble_length = len(message) + 2
    return f"""
 {"_" * bubble_length}
( {message} )    
 {"‾" * bubble_length}"""


def run():
    arguments = parse_arguments()
    setup_logging(arguments.log)
    logging.info("Start Deployer Application")
    config_file = arguments.conf
    action = arguments.action if arguments.action else 'deploy'
    apps = [item.strip() for item in arguments.appl.split(",")] if arguments.appl else None

    config = load_config(config_file)
    # Gets the application to perform the action on, defaults to all applications in the json config file
    applications = [app for app in config["applications"] if app["name"] in apps] if apps else  config["applications"]

    base_url = config.get("baseUrl")
    token = config.get("token")

    headers = {"authorization": f"Bearer {token}"} if token else None

    environment_url = f"{base_url}/architecture/environments"
    mesh_url = f"{base_url}/architecture/eventMeshes"
    messaging_services_url = f"{base_url}/architecture/messagingServices"
    domain_url= f"{base_url}/architecture/applicationDomains"
    application_url= f"{base_url}/architecture/applications"
    application_version_url= f"{base_url}/architecture/applicationVersions"
    deploy_url = f"{base_url}/architecture/runtimeManagement/applicationDeployments"

    environment_id = fetch_property(environment_url, headers, None, "id", "name", config["environmentName"])
    logging.info(f"Environment { config['environmentName'] }  with environmentId: { environment_id }")

    mesh_id = fetch_property(mesh_url, headers, {"environmentId": environment_id}, "id", "name", config["memName"])
    logging.info(f"Mesh { config['memName'] } with meshId: { mesh_id }")

    broker_ids = fetch_property(messaging_services_url, headers, {"eventMeshId": mesh_id}, None, None, None, "$..messagingServiceId")
    logging.info(f"brokerIds: { broker_ids }")

    domain_id = fetch_property(domain_url, headers, {"name": config["domainName"]}, "id")
    logging.info(f"Domain { config['domainName'] } with domainId: { domain_id }\n")

    logging.info(f"{action.capitalize()}ing applications: { [app['name'] for app in applications] }\n")

    for application in applications:
        application_id = fetch_property(application_url, headers, {"applicationDomainId": domain_id}, "id", "name", application["name"] )
        path_expr = f"$[?(@.version == '{ application['version'] }')]"
        application_version = fetch_property(application_version_url, headers=headers, params={"applicationIds": application_id}, path_expr=path_expr)
        logging.debug(f"applicationVersion= { application_version }")
        if is_version_eligible(config["environment"], action,  application_version[0]):
            application_version_id = fetch_property(application_version_url, headers, {"applicationIds": application_id}, "id", "version", application["version"] )
            logging.info(f"{action.capitalize()}ing application {application['name']}:{ application_id } and version { application['version'] }:{ application_version_id }")
            for broker_id in broker_ids:
                execute_action(deploy_url, headers, action, application, application_version_id, broker_id)
        else:
            logging.info(f"Application {application['name']} version { application['version'] } not eligible for action {action}! Skipping this version")
