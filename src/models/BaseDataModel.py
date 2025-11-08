from helpers.config import get_settings , Settings

class BaseDataModel:

    def __init__(self, db_client: object):
        self.db_clinet = db_client
        self.app_settings = get_settings()
