"""pact tests for user service client"""
import asyncio
import os.path
from multiprocessing import Process

import aiohttp
import pytest
import uvicorn

from configuration.config import pact_config, mock_server_data
from configuration.logging_setup import logger
from source.exceptions.service_exceptions import PactVerifierNotFoundError, PactVerificationError
from tests.contract_test.configuration.configuration import PactBrokerConfig
from tests.contract_test.configuration.provider_states_api import pact_router
from tests.contract_test.configuration.provider_states_setup import server_start_time, app


class MockServer:
    """ Create mock server for contract testing """

    def __init__(self):
        self.proc = None

    async def start_server(self):
        """ Bring mock server up. """
        app.include_router(pact_router, tags=["pact_api"])

        self.proc = Process(target=uvicorn.run,
                            args=(app,),
                            kwargs={
                                "host": mock_server_data.MOCK_SERVER_HOST,
                                "port": mock_server_data.MOCK_SERVER_PORT,
                                "log_level": "info"},
                            daemon=True)
        self.proc.start()
        # wait for the server to start
        await asyncio.sleep(server_start_time)

    def stop_server(self):
        """ Shutdown the app mock server. """
        if self.proc is not None:
            self.proc.terminate()
            self.proc.join()


@pytest.fixture
def broker_opts() -> PactBrokerConfig:
    """
        Generate the configuration for the Pact Broker.

        This fixture function generates a configuration object for the Pact Broker, which includes the broker
        username, password, URL, publish version, and whether to publish verification results.

        Returns:
            PactBrokerConfig: The configuration for the Pact Broker.
    """
    return PactBrokerConfig(
        broker_username=pact_config.PACT_BROKER_USERNAME,
        broker_password=pact_config.PACT_BROKER_PASSWORD,
        broker_url=pact_config.PACT_BROKER_URL,
        publish_version=pact_config.PUBLISH_VERSION,
        publish_verification_results=True
    )


async def run_pact_verifier():
    """
    Run the pact verifier to test if the provider respects
    the contract defined in consumer
    """
    try:
        cmd = [
            'pact-verifier',
            '--provider-base-url', mock_server_data.MOCKSERVER_URL,
            '--pact-broker-url', pact_config.PACT_BROKER_URL,
            '--provider', pact_config.PROVIDER_NAME,
            '--pact-broker-username', pact_config.PACT_BROKER_USERNAME,
            '--pact-broker-password', pact_config.PACT_BROKER_PASSWORD,
            '--provider-app-version', pact_config.PUBLISH_VERSION,
            '--publish-verification-results',
            '--verbose',
            '--provider-states-setup-url', os.path.join(mock_server_data.MOCKSERVER_URL, "_pact/provider_states"),
            '--enable-pending',
        ]
        process = await asyncio.create_subprocess_exec(*cmd,
                                                       stdout=asyncio.subprocess.PIPE,
                                                       stderr=asyncio.subprocess.PIPE)

        stdout, stderr = await process.communicate()
        if process.returncode == 0 and "failed" not in stdout.decode():
            logger.info("Pact verification succeeded.")
        else:
            logger.info("Pact verification failed. Please check the logs for details.")
            raise PactVerificationError("Pact verification failed.")

    except FileNotFoundError:
        logger.info("Pact Verifier is not installed or not in PATH.")
        raise PactVerifierNotFoundError("Pact Verifier not found.")


@pytest.mark.asyncio
async def test_pact_provider(broker_opts):
    """ Fetch an endpoint from the app. """
    mock_server = MockServer()
    await mock_server.start_server()
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(os.path.join(mock_server_data.MOCKSERVER_URL, "healthz")) as response:
                health_check = await response.json()
        assert health_check
        await run_pact_verifier()
    finally:
        mock_server.stop_server()
