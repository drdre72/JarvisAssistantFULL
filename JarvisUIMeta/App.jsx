// src/App.jsx
import React, { useState } from "react";
import ChatPanel from "./components/ChatPanel";
import SettingsDropdown from "./components/SettingsDropdown";
import MindMapPanel from "./components/MindMapPanel";

export default function App() {
  return (
    <div
      className="w-screen h-screen relative"
      style={{
        backgroundImage: "url('./JarvisShield.jpg')",
        backgroundSize: "cover",
        backgroundPosition: "center"
      }}
    >
      {/* Top Nav Bar */}
      <div className="flex justify-between items-center px-6 py-2 bg-black/30">
        <div className="flex gap-4 items-center">
          <span className="text-xl text-orange-400 font-bold">J.A.R.V.I.S.</span>
          <input
            className="bg-black/70 text-white px-3 py-1 rounded ml-2"
            placeholder="What can I search for you, sir?"
          />
        </div>
        <div className="flex gap-3">
          <button>Settings</button>
          <button>Restart</button>
          <button>Shutdown</button>
          <button>Logoff</button>
        </div>
      </div>
      {/* Main content */}
      <div className="flex h-[calc(100vh-50px)]">
        {/* Left Side Shortcuts */}
        <div className="w-1/6 flex flex-col gap-2 py-8">
          {/* Map your shortcuts here */}
          <button className="bg-black/40 text-orange-300 rounded px-2 py-1 mb-2">Steam</button>
          {/* ...other shortcuts */}
        </div>
        {/* Center: Chat, clock, system info */}
        <div className="flex-1 flex flex-col items-center justify-center relative">
          {/* Clock */}
          <div className="text-6xl text-white font-mono drop-shadow mb-4">11:47</div>
          {/* System status, etc. */}
          <div className="text-white/70 mb-6">Currently power level is at <span className="text-green-400">100%</span></div>
          {/* Chat panel */}
          <ChatPanel />
        </div>
        {/* Right Side Panels */}
        <div className="w-1/6 flex flex-col items-end py-8">
          <SettingsDropdown />
          <MindMapPanel />
          {/* More future tools */}
        </div>
      </div>
      {/* Bottom Bar (optional) */}
      <div className="absolute bottom-0 w-full flex justify-end items-center bg-black/40 p-2">
        {/* Music, system info */}
        <span className="text-white">ENG 11:47</span>
      </div>
    </div>
  );
}
