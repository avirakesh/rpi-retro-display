from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel
import asyncio


class Brightness(BaseModel):
    brightness: float


class Server:
    def __init__(self, brightness_update_queue: asyncio.Queue[Brightness]):
        self.app = FastAPI()
        self._brightness_update_queue = brightness_update_queue
        self._setup_routes()

    def _setup_routes(self):
        # Define routes here
        @self.app.post("/brightness")
        async def set_brightness(brightness: Brightness):
            if brightness.brightness < 0 or brightness.brightness > 1:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Brightness must be in range [0, 1], "
                    f"but received {brightness.brightness}",
                )
            try:
                while not self._brightness_update_queue.empty():
                    self._brightness_update_queue.getnowait()
            except asyncio.QueueEmpty:
                # Expected, we're draining the queue
                pass

            # Add the new brightness value to the queue
            await self._brightness_update_queue.put(brightness)
            return {
                "message": f"Brightness successfully updated to {brightness.brightness}"
            }
