import asyncio
import time
import os

from dotenv import load_dotenv
load_dotenv(".env.local")

from livekit import agents
from livekit.agents import Agent, AgentServer, AgentSession
from livekit.plugins import deepgram, groq, rime


# =========================================
# AGENT
# =========================================

class RimeVoiceAgent(Agent):

    def __init__(self):
        super().__init__(
            instructions=(
                "Support English and Hindi voice conversations. "
                "If the user speaks in Hindi, respond in Hindi. "
                "If the user speaks in English, respond in English. "
                "If the user mixes Hindi and English, naturally respond in the same mixed language style. "

                "Treat 'start a task' as an immediate command. "
                "Do not ask what task the user means. "

                "You are a realtime voice assistant. "
                "Answer in short, complete sentences. "
                "Keep normal answers under 2 sentences. "
                "Do not use markdown, tables, bullet points, or special symbols. "
                "Speak naturally and clearly. "

                "If the user asks how to pronounce a word, name, "
                "technical term, or phrase, first say the exact term "
                "clearly, then give a short pronunciation explanation. "
                "Do not give a long explanation. "

                "The user can interrupt you at any time."
            )
        )

        self.current_task = None
        self.task_id = 0
        self.task_status = "idle"
        self.last_user_finished = None
        self.interruption_id = 0
        self.response_start_time = None


    # =========================================
    # LONG RUNNING TASK
    # =========================================

    async def run_long_task(self, task_id):

        print(f"[TASK] Started task #{task_id}")

        try:
            await asyncio.sleep(30)

            if task_id != self.task_id:
                print(
                    f"[TASK] Task #{task_id} is stale - ignoring result"
                )
                return

            self.task_status = "completed"

            print(
                f"[TASK] Finished task #{task_id}"
            )

        except asyncio.CancelledError:

            print(
                f"[TASK] Task #{task_id} CANCELLED"
            )

            return

        finally:

            if task_id == self.task_id:
                self.current_task = None


    # =========================================
    # START TASK
    # =========================================

    def start_task(self):

        if self.current_task and not self.current_task.done():

            print("[TASK] Already running")

            return

        self.task_id += 1

        current_id = self.task_id

        self.task_status = "running"

        print(
            f"[TASK] Creating task #{current_id}"
        )

        self.current_task = asyncio.create_task(
            self.run_long_task(current_id)
        )

        print(
            "[TASK] Long-running task started. "
            "Ready for interruption."
        )


    # =========================================
    # CANCEL TASK
    # =========================================

    def cancel_current_task(self):

        if self.current_task and not self.current_task.done():

            print(
                f"[TASK] Cancelling task #{self.task_id}"
            )

            self.task_status = "cancelled"

            self.task_id += 1

            self.current_task.cancel()

            self.current_task = None

        else:

            print(
                "[TASK] No active task to cancel"
            )


    # =========================================
    # INTERRUPTION
    # =========================================

    def mark_interruption(self):

        self.interruption_id += 1

        print(
            f"[INTERRUPTION] {time.perf_counter():.3f}"
        )

        if self.current_task and not self.current_task.done():

            print(
                "[INTERRUPTION] Cancelling background task"
            )

            self.task_status = "cancelled"

            self.task_id += 1

            self.current_task.cancel()

            self.current_task = None

        else:

            print(
                "[INTERRUPTION] No background task running"
            )


# =========================================
# SERVER
# =========================================

server = AgentServer()


@server.rtc_session(agent_name="rime-voice-agent")
async def entrypoint(ctx: agents.JobContext):

    # =========================================
    # SESSION
    # =========================================

    session = AgentSession(

        stt=deepgram.STT(
            model="nova-3",
            language="multi",
        ),

        llm=groq.LLM(
            model="openai/gpt-oss-20b",
            api_key=os.getenv("GROQ_API_KEY"),
            parallel_tool_calls=False,
            tool_choice="auto",
        ),

        tts=rime.TTS(
            model="coda",
            speaker="astra",
            api_key=os.getenv("RIME_API_KEY"),
            sample_rate=24000,
            use_websocket=True,
        ),

        turn_handling={
            "interruption": {
                "mode": "vad",
                "resume_false_interruption": False,
                "min_duration": 0.15,
                "min_words": 0,
                "discard_audio_if_uninterruptible": True,
            },
        },
    )


    # =========================================
    # CREATE AGENT
    # =========================================

    agent = RimeVoiceAgent()

    await session.start(
        room=ctx.room,
        agent=agent
    )


    # =========================================
    # OVERLAPPING SPEECH
    # =========================================

    @session.on("overlapping_speech")
    def on_overlapping_speech(event):

        print(
            f"[OVERLAP] interruption={event.is_interruption} "
            f"probability={event.probability:.2f}"
        )

        if event.is_interruption:

            print(
                "[INTERRUPTION] STOPPING RIME SPEECH"
            )

            session.interrupt(force=True)

            agent.mark_interruption()


    # =========================================
    # USER TRANSCRIPTION
    # =========================================

    @session.on("user_input_transcribed")
    def on_user_input_transcribed(event):

        print(
            f"[USER INPUT] {event.transcript}"
        )


        # -----------------------------------------
        # FINAL TRANSCRIPT
        # -----------------------------------------

        if event.is_final:

            agent.last_user_finished = (
                time.perf_counter()
            )


        # -----------------------------------------
        # PARTIAL TRANSCRIPT
        # -----------------------------------------

        if not event.is_final:

            if event.transcript.strip():

                print(
                    "[INTERRUPTION] "
                    "Speech detected - stopping Rime"
                )

                interruption_time = (
                    time.perf_counter()
                )

                session.interrupt(force=True)

                agent.mark_interruption()

                stop_time = (
                    time.perf_counter()
                )

                print(
                    f"[METRIC] Interruption stop latency: "
                    f"{(stop_time - interruption_time) * 1000:.1f} ms"
                )

            return


        # -----------------------------------------
        # FINAL USER TEXT
        # -----------------------------------------

        text = event.transcript.lower().strip()

        print(
            f"[USER FINAL] {text}"
        )


        # -----------------------------------------
        # OLD PROCESSING METRIC
        # -----------------------------------------

        if agent.last_user_finished:

            print(
                f"[METRIC] User-to-processing latency: "
                f"{(time.perf_counter() - agent.last_user_finished) * 1000:.1f} ms"
            )


        # -----------------------------------------
        # CANCEL ACTIVE TASK
        # -----------------------------------------

        if (
            agent.current_task
            and not agent.current_task.done()
        ):

            print(
                "[TASK] New user request detected - "
                "cancelling old task"
            )

            agent.cancel_current_task()


        # -----------------------------------------
        # START TASK COMMAND
        # -----------------------------------------

        if (
            "long task" in text
            or "start a task" in text
            or "start task" in text
        ):

            print(
                "[COMMAND] Starting long-running task"
            )

            agent.start_task()


        # -----------------------------------------
        # STOP TASK COMMAND
        # -----------------------------------------

        elif (
            text.startswith("stop")
            or text.startswith("cancel")
            or "cancel task" in text
            or "stop task" in text
        ):

            print(
                "[COMMAND] Cancelling task"
            )

            agent.cancel_current_task()


    # =========================================
    # REAL RESPONSE LATENCY
    # =========================================

    @session.on("conversation_item_added")
    def on_conversation_item_added(event):

        if event.item.role == "assistant":

            if agent.last_user_finished:

                latency = (
                    time.perf_counter()
                    - agent.last_user_finished
                ) * 1000

                print(
                    f"[METRIC] User-to-assistant latency: "
                    f"{latency:.1f} ms"
                )


    # =========================================
    # INITIAL GREETING
    # =========================================

    await session.generate_reply(
        instructions=(
            "Give a brief explanation of how you can help "
            "the user. Tell them they can interrupt you at "
            "any time with a new request. "
            "Do not ask the user any questions."
        )
    )


# =========================================
# RUN APPLICATION
# =========================================

if __name__ == "__main__":

    agents.cli.run_app(server)