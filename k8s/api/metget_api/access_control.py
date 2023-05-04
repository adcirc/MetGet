class AccessControl:
    """
    This class is used to check if the user is authorized to use the API
    """

    def __init__(self):
        """
        This method is used to initialize the class. It creates a database
        connection and a session object
        """
        from metbuild.database import Database

        self.__db = Database()
        self.__session = self.__db.session()

    @staticmethod
    def hash_access_token(token: str) -> str:
        """
        This method is used to hash the access token before comparison
        """
        from hashlib import sha256

        return sha256(token.encode()).hexdigest()

    def is_authorized(self, api_key: str) -> bool:
        """
        This method is used to check if the user is authorized to use the API
        The method returns True if the user is authorized and False if not
        Keys are hashed before being compared to the database to prevent
        accidental exposure of the keys and/or sql injection
        """
        from metbuild.tables import AuthTable

        api_key_hash = AccessControl.hash_access_token(str(api_key))
        api_key_db = (
            self.__session.query(AuthTable.id, AuthTable.key)
            .filter_by(key=api_key)
            .first()
        )

        if api_key_db is None:
            return False

        api_key_db_hash = AccessControl.hash_access_token(api_key_db.key.strip())

        if api_key_db_hash == api_key_hash:
            return True
        else:
            return False

    @staticmethod
    def check_authorization_token(headers) -> bool:
        """
        This method is used to check if the user is authorized to use the API
        The method returns True if the user is authorized and False if not
        """
        user_token = headers.get("x-api-key")
        gatekeeper = AccessControl()
        if gatekeeper.is_authorized(user_token):
            return True
        else:
            return False

    @staticmethod
    def unauthorized_response():
        status = 401
        return {
            "statusCode": status,
            "body": {"message": "ERROR: Unauthorized"},
        }, status

    @staticmethod
    def get_credit_balance(api_key: str) -> dict:
        """
        This method is used to get the credit balance for the user

        Args:
            api_key (str): The API key used to authenticate the request

        Returns:
            dict: A dictionary containing the credit limit, credits used, and credit balance
        """
        from metbuild.tables import RequestTable
        from metbuild.tables import AuthTable
        from metbuild.database import Database
        from datetime import datetime, timedelta
        from sqlalchemy import func, or_

        credit_multiplier = 100000.0

        db = Database()
        session = db.session()

        # ...Queries the database for the credit limit for the user
        credit_limit = (
            session.query(AuthTable.credit_limit).filter_by(key=api_key).first()[0]
        )
        credit_limit = float(credit_limit) / credit_multiplier

        # ...Queries the database for the credit used for the user over the last 30 days
        start_date = datetime.utcnow() - timedelta(days=30)
        credit_used = (
            session.query(func.sum(RequestTable.credit_usage))
            .filter(RequestTable.last_date >= start_date)
            .filter(RequestTable.api_key == api_key)
            .filter(
                or_(
                    RequestTable.status == "completed", RequestTable.status == "running"
                )
            )
            .first()[0]
        )

        if credit_used is None:
            credit_used = 0.0
        else:
            credit_used = float(credit_used) / credit_multiplier

        credit_balance = credit_limit - credit_used

        return {
            "credit_limit": credit_limit,
            "credits_used": credit_used,
            "credit_balance": credit_balance,
        }
