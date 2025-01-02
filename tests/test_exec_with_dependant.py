import fastapi
import pytest

from fastexec import exec_with_dependant, get_dependant


@pytest.mark.asyncio
async def test_exec_with_dependant():

    def get_config():
        config = {
            "app_name": "DAG Processor",
            "db_connection_string": "sqlite:///./test.db",
            "api_key": "secret_api_key",
        }
        print("Config initialized.")
        return config

    def get_db(config: dict = fastapi.Depends(get_config)):
        db_connection = f"Connected to database with {config['db_connection_string']}"
        print("Database connection established.")
        return db_connection

    def get_auth_service(config: dict = fastapi.Depends(get_config)):
        auth_service = f"Auth service initialized with API key {config['api_key']}"
        print("Authentication service initialized.")
        return auth_service

    # --- DAG Tasks ---

    def initialize_resources(
        db: str = fastapi.Depends(get_db),
        auth_service: str = fastapi.Depends(get_auth_service),
    ):
        print(f"Initializing resources with DB: {db} and Auth: {auth_service}")
        return {"resources_initialized": True}

    def process_data(initialization: dict = fastapi.Depends(initialize_resources)):
        print("Processing data...")
        # Simulate data processing
        processed_data = {"data": "Processed Data"}
        print("Data processed.")
        return processed_data

    def save_results(
        data: dict = fastapi.Depends(process_data),
        db: str = fastapi.Depends(get_db),
    ):
        print(f"Saving results to DB: {db}")
        # Simulate saving data
        print(f"Results saved: {data}")
        return {"results_saved": True}

    async def notify_completion(
        request: fastapi.Request,
        body: dict = fastapi.Body(default_factory=dict),
        save: dict = fastapi.Depends(save_results),
        auth_service: str = fastapi.Depends(get_auth_service),
    ):
        print("path_params:", request.path_params)
        print("query_params:", request.query_params)
        print("headers:", request.headers)
        print("body:", body)
        print("body:", await request.body())
        print(f"Notifying via {auth_service} that processing is complete.")
        return {"notification_sent": True}

    dependant = get_dependant(path="/", call=notify_completion)
    result = await exec_with_dependant(
        dependant=dependant,
        query_params={"key1": "value1", "key2": "value2", "key3": "value3"},
        headers={
            "Content-Type": "application/json",
            "Authorization": "Bearer your_token_here",
        },
        body={
            "name": "Sample Item",
            "description": "This is a sample item.",
            "price": 29.99,
            "tax": 2.5,
        },
    )
    print(result)
