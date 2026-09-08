# 🎙️ Rime Voice Task Agent

> A voice-native task agent built with Rime TTS, Deepgram STT, Groq, and LiveKit — designed for **instant interruption and recovery** during ongoing voice tasks.

**Hackathon:** Rime Hackathon — DataForge × Rime

### Core Voice Challenge

**Interruption & Recovery**

The user can interrupt the agent while it is speaking. The agent immediately stops the current Rime speech, cancels or invalidates the ongoing task, and processes the user's new instruction without continuing stale output.
# Rime Voice Agent — Voice Engineering Evidence

## 1. Hard Voice Problem

The project focuses on interruption and recovery in a realtime voice task agent.

The key problem is that users should be able to speak over the agent naturally. When the user interrupts, the agent should stop its current spoken response, cancel obsolete background work, and process the new instruction instead of continuing the old response.

Rime is used as the primary TTS system for the agent's spoken output.

---

## 2. Acceptance Test

### Interruption and Recovery Test

Test procedure:

1. Start the realtime voice agent.
2. Say: "Start a task."
3. The agent starts a simulated long-running background task.
4. While the agent is speaking, say: "Explain Python."
5. Verify that:
   - Current Rime speech is interrupted.
   - The background task is cancelled.
   - The old task does not continue producing a stale result.
   - The new user request is processed.
   - The agent responds to the new request.

### Observed Result

The test successfully produced:

- `[TASK] Started task`
- `[INTERRUPTION] Speech detected - stopping Rime`
- `[INTERRUPTION] Cancelling background task`
- `[TASK] Task #... CANCELLED`
- A new final transcript for "Explain Python."

This demonstrates interruption, speech stopping, background-task cancellation, and recovery.

---

## 3. Interruption Latency

The system records the time between interruption detection and the request to stop the current speech.

Observed measurements during testing included:

- 0.2 ms
- 0.3 ms
- 0.5 ms
- 1.3 ms
- 5.1 ms
- 6.4 ms

One active-task interruption produced:

`[METRIC] Interruption stop latency: 5.1 ms`

The measurements show that the application can issue the speech-stop request very quickly after detecting user speech.

---

## 4. Background Task Cancellation

The agent uses task IDs and cancellation to prevent obsolete work from continuing.

Example test:

```text
[TASK] Started task #3
[INTERRUPTION] Speech detected - stopping Rime
[INTERRUPTION] Cancelling background task
[TASK] Task #3 CANCELLED