import os
import uuid
import asyncio
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse, parse_qs

from dotenv import load_dotenv
from livekit import api

load_dotenv(".env.local")

LIVEKIT_API_KEY = os.getenv("LIVEKIT_API_KEY")
LIVEKIT_API_SECRET = os.getenv("LIVEKIT_API_SECRET")
LIVEKIT_URL = os.getenv("LIVEKIT_URL")

AGENT_NAME = "rime-voice-agent"


async def dispatch_agent(room):
    async with api.LiveKitAPI(
        url=LIVEKIT_URL,
        api_key=LIVEKIT_API_KEY,
        api_secret=LIVEKIT_API_SECRET,
    ) as lkapi:

        # Check whether this room already has a dispatch
        dispatches = await lkapi.agent_dispatch.list_dispatch(room)

        if dispatches:
            print(
                f"[DISPATCH] Agent already dispatched to {room}"
            )
            return dispatches[0]

        dispatch = await lkapi.agent_dispatch.create_dispatch(
            api.CreateAgentDispatchRequest(
                agent_name=AGENT_NAME,
                room=room,
            )
        )

        print(
            f"[DISPATCH] Agent dispatched to {room}: "
            f"{dispatch.id}"
        )

        return dispatch


class TokenHandler(BaseHTTPRequestHandler):

    def do_GET(self):

        path = urlparse(self.path).path

        if path == "/get-token":

            params = parse_qs(urlparse(self.path).query)

            room = params.get(
                "room",
                ["rime-demo-room"]
            )[0]

            # Dispatch the voice agent into this room
            try:
                asyncio.run(dispatch_agent(room))
            except Exception as e:
                print(
                    f"[DISPATCH ERROR] {e}"
                )

                self.send_response(500)
                self.send_header(
                    "Content-Type",
                    "application/json"
                )
                self.send_header(
                    "Access-Control-Allow-Origin",
                    "*"
                )
                self.end_headers()

                self.wfile.write(
                    b'{"error":"Agent dispatch failed"}'
                )

                return

            # Create browser participant identity
            identity = (
                f"user-{uuid.uuid4().hex[:8]}"
            )

            # Create LiveKit access token
            token = (
                api.AccessToken(
                    LIVEKIT_API_KEY,
                    LIVEKIT_API_SECRET,
                )
                .with_identity(identity)
                .with_name("Rime Voice User")
                .with_grants(
                    api.VideoGrants(
                        room_join=True,
                        room=room,
                        can_publish=True,
                        can_subscribe=True,
                    )
                )
                .to_jwt()
            )

            response = (
                '{"token":"' + token +
                '","url":"' + LIVEKIT_URL + '"}'
            )

            self.send_response(200)

            self.send_header(
                "Content-Type",
                "application/json"
            )

            self.send_header(
                "Access-Control-Allow-Origin",
                "*"
            )

            self.end_headers()

            self.wfile.write(
                response.encode("utf-8")
            )

        else:

            self.send_response(404)
            self.end_headers()

    def log_message(self, format, *args):
        print(
            "[TOKEN SERVER]",
            *args
        )


if __name__ == "__main__":
    PORT = int(os.getenv("PORT", "8000"))
    print(f"🔐 LiveKit token server running on port {PORT}")
    HTTPServer(("0.0.0.0", PORT), TokenHandler).serve_forever()