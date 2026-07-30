import asyncio
import structlog

from sota_dl.core.config_service import ConfigurationService
from sota_dl.core.event_bus import EventBus, OAuth2RequiredEvent
from sota_dl.infrastructure.network import NetworkManager

logger = structlog.get_logger(__name__)


class OAuth2DeviceFlowService:
    """Service to handle the OAuth2 Device Authorization Flow."""

    def __init__(
        self,
        config_service: ConfigurationService,
        event_bus: EventBus,
        network_service: NetworkManager,
    ):
        self._config = config_service
        self._event_bus = event_bus
        self._network = network_service
        # Fetching credentials from config_service instead of hardcoding
        self._client_id = self._config.get_oauth_client_id()
        self._client_secret = self._config.get_oauth_client_secret()

    async def initiate_flow(self) -> None:
        """Initiates the OAuth2 device flow and publishes the required event."""
        logger.info("Initiating OAuth2 device flow")

        # Google OAuth2 Device Flow endpoint
        device_code_url = "https://oauth2.googleapis.com/device/code"

        payload = {
            "client_id": self._client_id,
            "scope": "https://www.googleapis.com/auth/youtube.readonly",
        }

        try:
            response = await self._network.post_async(device_code_url, data=payload)
            response.raise_for_status()
            data = response.json()

            device_code = data["device_code"]
            user_code = data["user_code"]
            auth_url = data["verification_url"]

            # Publish event to UI
            await self._event_bus.publish(
                OAuth2RequiredEvent(
                    user_code=user_code, auth_url=f"{auth_url}?user_code={user_code}"
                )
            )

            # Start polling in background
            asyncio.create_task(self._poll_for_token(device_code))

        except Exception as e:
            logger.error("Failed to initiate OAuth2 flow", error=str(e))
            raise e

    async def _poll_for_token(self, device_code: str) -> None:
        """Polls for authorization tokens."""
        logger.info("Polling for token")
        token_url = "https://oauth2.googleapis.com/token"  # nosec

        payload = {
            "client_id": self._client_id,
            "client_secret": self._client_secret,
            "device_code": device_code,
            "grant_type": "urn:ietf:params:oauth:grant-type:device_code",
        }

        # Simplified polling loop
        for _ in range(30):  # Adjust polling attempts as needed
            await asyncio.sleep(5)  # Poll interval
            try:
                response = await self._network.post_async(token_url, data=payload)
                if response.status_code == 200:
                    data = response.json()
                    logger.info("Successfully obtained tokens")
                    # Store tokens using config_service
                    self._config.store_oauth_tokens(
                        data["access_token"], data["refresh_token"]
                    )
                    break
                elif response.status_code == 400:
                    error = response.json().get("error")
                    if error == "authorization_pending":
                        continue
                    else:
                        logger.error("OAuth2 error", error=error)
                        break
            except Exception as e:
                logger.error("Polling error", error=str(e))
                break
