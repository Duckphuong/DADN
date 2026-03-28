from flask import current_app

from app.bootstrap.container import ApplicationContainer, CONTAINER_EXTENSION_KEY


def get_container() -> ApplicationContainer:
    return current_app.extensions[CONTAINER_EXTENSION_KEY]
