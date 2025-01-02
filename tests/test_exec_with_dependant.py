import fastapi
import pytest

from fastexec import exec_with_dependant, get_dependant


@pytest.mark.asyncio
async def test_exec_with_dependant():
    # Configuration setup
    config = {
        "app_name": "DAG Processor",
        "db_connection_string": "sqlite:///./test.db",
        "api_key": "secret_api_key",
    }

    def get_config():
        return config

    def get_db(config: dict = fastapi.Depends(get_config)):
        return f"Connected to database with {config['db_connection_string']}"

    def get_auth_service(config: dict = fastapi.Depends(get_config)):
        return f"Auth service initialized with API key {config['api_key']}"

    def initialize_resources(
        db: str = fastapi.Depends(get_db),
        auth_service: str = fastapi.Depends(get_auth_service),
        config: dict = fastapi.Depends(get_config),
    ):
        return {
            **config,
            "resources_initialized": True,
            "db": db,
            "auth_service": auth_service,
        }

    def process_data(initialization: dict = fastapi.Depends(initialize_resources)):
        return {
            **initialization,
            "processed_data": {"data": "Processed Data"},
        }

    def save_results(
        data: dict = fastapi.Depends(process_data),
        db: str = fastapi.Depends(get_db),
    ):
        return {
            **data,
            "results_saved": True,
        }

    async def notify_completion(
        request: fastapi.Request,
        body: dict = fastapi.Body(default_factory=dict),
        save: dict = fastapi.Depends(save_results),
        auth_service: str = fastapi.Depends(get_auth_service),
    ):
        return {
            **save,
            "notification_sent": True,
        }

    # Execute the dependant function
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

    # Assertions to verify the expected outcomes
    assert (
        result.get("notification_sent") is True
    ), "Notification was not sent successfully."
    assert (
        result.get("resources_initialized") is True
    ), "Resources were not initialized."
    assert result.get("processed_data") == {
        "data": "Processed Data"
    }, "Data was not processed correctly."
    assert result.get("results_saved") is True, "Results were not saved."
    assert (
        result.get("db") == "Connected to database with sqlite:///./test.db"
    ), "Database connection string mismatch."
    assert (
        result.get("auth_service")
        == "Auth service initialized with API key secret_api_key"
    ), "Auth service initialization failed."
