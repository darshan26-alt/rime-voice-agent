import {
  LiveKitRoom,
  RoomAudioRenderer,
  StartAudio,
  useConnectionState,
  useRoomContext,
  TrackToggle,
} from "@livekit/components-react";
import "@livekit/components-styles";
import { useEffect, useRef, useState } from "react";
import "./App.css";

const TOKEN_URL =
  "https://rime-voice-agent-l8wv.onrender.com/get-token?room=rime-demo-room";


function VoiceDashboard() {
  const room = useRoomContext();
  const connectionState = useConnectionState();

  const [status, setStatus] = useState("READY");
  const [messages, setMessages] = useState([]);
  const [taskStatus, setTaskStatus] = useState("IDLE");

  const messagesEndRef = useRef(null);


  // =========================================
  // TRANSCRIPT LISTENER
  // =========================================

  useEffect(() => {

    const handleTranscription = async (
      reader,
      participantInfo
    ) => {

      try {

        const text = await reader.readAll();

        if (!text?.trim()) return;

        const isUser =
          participantInfo.identity ===
          room.localParticipant.identity;

        console.log(
          "[TRANSCRIPT]",
          isUser ? "USER:" : "AGENT:",
          text
        );

        setMessages((prev) => [
          ...prev,
          {
            id: `${Date.now()}-${Math.random()}`,
            role: isUser ? "user" : "assistant",
            text: text.trim(),
          },
        ]);

      } catch (error) {

        console.error(
          "[TRANSCRIPT ERROR]",
          error
        );

      }

    };


    room.registerTextStreamHandler(
      "lk.transcription",
      handleTranscription
    );


    return () => {

      room.unregisterTextStreamHandler(
        "lk.transcription"
      );

    };

  }, [room]);


  // =========================================
  // AUTO SCROLL
  // =========================================

  useEffect(() => {

    messagesEndRef.current?.scrollIntoView({
      behavior: "smooth",
    });

  }, [messages]);


  // =========================================
  // CONNECTION STATUS
  // =========================================

  useEffect(() => {

    if (connectionState === "connected") {

      setStatus("CONNECTED");

    } else if (
      connectionState === "connecting"
    ) {

      setStatus("CONNECTING");

    } else {

      setStatus("DISCONNECTED");

    }

  }, [connectionState]);


  // =========================================
  // TASK STATUS FROM USER COMMANDS
  // =========================================

  useEffect(() => {

    const lastMessage =
      messages[messages.length - 1];

    if (
      !lastMessage ||
      lastMessage.role !== "user"
    ) {
      return;
    }

    const text =
      lastMessage.text.toLowerCase();


    // START TASK

    if (
      text.includes("start a task") ||
      text.includes("start task") ||
      text.includes("long task")
    ) {

      setTaskStatus("RUNNING");

    }


    // INTERRUPTION / CANCELLATION

    if (
      text.includes("stop") ||
      text.includes("cancel") ||
      text.includes("interrupt") ||
      text.includes("explain")
    ) {

      if (taskStatus === "RUNNING") {

        setTaskStatus("CANCELLED");

      }

    }

  }, [messages, taskStatus]);


  // =========================================
  // TASK STATUS HELPERS
  // =========================================

  const getTaskClass = () => {

    if (taskStatus === "RUNNING") {
      return "task-running";
    }

    if (taskStatus === "CANCELLED") {
      return "task-cancelled";
    }

    if (taskStatus === "COMPLETED") {
      return "task-completed";
    }

    return "task-idle";

  };


  const getTaskIcon = () => {

    if (taskStatus === "RUNNING") {
      return "🔄";
    }

    if (taskStatus === "CANCELLED") {
      return "⛔";
    }

    if (taskStatus === "COMPLETED") {
      return "✅";
    }

    return "○";

  };


  return (

    <div className="app">

      {/* =====================================
          HEADER
      ===================================== */}

      <header className="header">

        <div>

          <h1>
            🎙️ Rime Voice Task Agent
          </h1>

          <p>
            Voice-native assistant with
            instant interruption & recovery
          </p>

        </div>


        <div
          className={`status ${status.toLowerCase()}`}
        >
          ● {status}
        </div>

      </header>


      <main className="main">

        {/* =================================
            VOICE CONTROL
        ================================= */}

        <section className="voice-card">

          <div
            className={`mic-wrapper ${
              status === "LISTENING"
                ? "active"
                : ""
            }`}
          >

            <TrackToggle
              source="microphone"
              className="mic-circle"

              onChange={(enabled) => {

                setStatus(
                  enabled
                    ? "LISTENING"
                    : "CONNECTED"
                );

              }}

              aria-label="Toggle microphone"
            >
              🎤
            </TrackToggle>

          </div>


          <h2>

            {status === "LISTENING"
              ? "Listening..."
              : "Click to Speak"}

          </h2>


          <p>
            Speak naturally and interrupt
            the agent anytime.
          </p>


          <div className="voice-hint">
            ⚡ Instant interruption enabled
          </div>

        </section>


        {/* =================================
            CONVERSATION
        ================================= */}

        <section className="conversation-card">

          <div className="conversation-header">

            <h2>
              Conversation
            </h2>

            <span className="live-dot">
              ● LIVE
            </span>

          </div>


          <div
            className="messages"
            aria-live="polite"
          >

            {messages.length === 0 ? (

              <div className="empty">

                <div className="empty-icon">
                  💬
                </div>

                <p>
                  Your conversation will
                  appear here.
                </p>

                <small>
                  Try saying "Start a task"
                </small>

              </div>

            ) : (

              messages.map((message) => (

                <div
                  className={`message ${message.role}`}
                  key={message.id}
                >

                  <div className="message-header">

                    <strong>
                      {message.role === "user"
                        ? "You"
                        : "Agent"}
                    </strong>

                  </div>

                  <span>
                    {message.text}
                  </span>

                </div>

              ))

            )}

            <div ref={messagesEndRef} />

          </div>

        </section>


        {/* =================================
            TASK EXECUTION
        ================================= */}

        <section className="task-panel">

          <div className="task-panel-header">

            <div>

              <h2>
                ⚡ Task Execution
              </h2>

              <p>
                Live interruption & recovery pipeline
              </p>

            </div>


            <div
              className={`task-badge ${getTaskClass()}`}
            >

              {getTaskIcon()}{" "}

              {taskStatus === "IDLE"
                ? "READY"
                : taskStatus}

            </div>

          </div>


          <div className="demo-flow">

            {/* VOICE COMMAND */}

            <div className="demo-step">

              <div className="demo-icon">
                🎙️
              </div>

              <strong>
                Voice Command
              </strong>

              <span>
                Start a task
              </span>

            </div>


            <div className="demo-arrow">
              →
            </div>


            {/* TASK RUNNING */}

            <div
              className={`demo-step ${
                taskStatus === "RUNNING"
                  ? "active-demo-step"
                  : "running"
              }`}
            >

              <div className="demo-icon">
                ⚙️
              </div>

              <strong>
                Task Running
              </strong>

              <span>
                Long-running work
              </span>

            </div>


            <div className="demo-arrow">
              →
            </div>


            {/* INTERRUPT */}

            <div className="demo-step interrupt">

              <div className="demo-icon">
                ✋
              </div>

              <strong>
                Interrupt
              </strong>

              <span>
                Speak anytime
              </span>

            </div>


            <div className="demo-arrow">
              →
            </div>


            {/* CANCELLED */}

            <div
              className={`demo-step ${
                taskStatus === "CANCELLED"
                  ? "active-demo-step"
                  : "cancelled"
              }`}
            >

              <div className="demo-icon">
                ⛔
              </div>

              <strong>
                Cancelled
              </strong>

              <span>
                Stale work stopped
              </span>

            </div>


            <div className="demo-arrow">
              →
            </div>


            {/* RECOVERY */}

            <div className="demo-step recovery">

              <div className="demo-icon">
                🔊
              </div>

              <strong>
                Recovery
              </strong>

              <span>
                New request spoken
              </span>

            </div>

          </div>


          {/* =================================
              HIGHLIGHT
          ================================= */}

          <div className="demo-highlight">

            <div className="highlight-icon">
              ⚡
            </div>


            <div>

              <strong>
                Instant Interruption
              </strong>

              <p>
                Rime speech stops immediately,
                the active task is cancelled,
                and the agent is ready for the
                user's next command.
              </p>

            </div>

          </div>

        </section>


        {/* =================================
            METRICS
        ================================= */}

        <section className="metrics">

          <div className="metric">

            <span>
              LiveKit
            </span>

            <strong>

              {connectionState === "connected"
                ? "✓ Connected"
                : "○ Waiting"}

            </strong>

          </div>


          <div className="metric">

            <span>
              Interruption
            </span>

            <strong>
              ✓ Ready
            </strong>

            <small>
              Speak anytime to interrupt
            </small>

          </div>


          <div className="metric">

            <span>
              Rime TTS
            </span>

            <strong>
              ✓ Active
            </strong>

            <small>
              Primary voice output
            </small>

          </div>


          <div className="metric">

            <span>
              Voice Mode
            </span>

            <strong>
              🎙️ Hands-Free
            </strong>

            <small>
              Real-time voice interaction
            </small>

          </div>


          <div className="metric">

            <span>
              Messages
            </span>

            <strong>
              {messages.length}
            </strong>

            <small>
              Conversation events
            </small>

          </div>

        </section>

      </main>


      <RoomAudioRenderer />

      <StartAudio label="Enable audio" />

    </div>

  );
}


/* =========================================
   APP
========================================= */

export default function App() {

  const [token, setToken] =
    useState(null);

  const [serverUrl, setServerUrl] =
    useState(null);

  const [error, setError] =
    useState(null);


  useEffect(() => {

    fetch(TOKEN_URL)

      .then((response) => {

        if (!response.ok) {

          throw new Error(
            "Token server returned an error"
          );

        }

        return response.json();

      })

      .then((data) => {

        setToken(data.token);
        setServerUrl(data.url);

      })

      .catch((err) => {

        console.error(
          "[TOKEN ERROR]",
          err
        );

        setError(
          "Could not connect to the token server. Make sure token_server.py is running."
        );

      });

  }, []);


  // =========================================
  // ERROR
  // =========================================

  if (error) {

    return (

      <div className="app">

        <div className="error">

          <h2>
            ⚠️ Connection Error
          </h2>

          <p>
            {error}
          </p>

          <button
            onClick={() =>
              window.location.reload()
            }
          >
            Retry
          </button>

        </div>

      </div>

    );

  }


  // =========================================
  // LOADING
  // =========================================

  if (!token || !serverUrl) {

    return (

      <div className="app">

        <div className="loading">

          <h2>
            Connecting to Rime Voice Agent...
          </h2>

          <p>
            Getting a secure LiveKit connection...
          </p>

        </div>

      </div>

    );

  }


  // =========================================
  // LIVEKIT ROOM
  // =========================================

  return (

    <LiveKitRoom
      token={token}
      serverUrl={serverUrl}
      connect={true}
      audio={true}
      video={false}
    >

      <VoiceDashboard />

    </LiveKitRoom>

  );

}