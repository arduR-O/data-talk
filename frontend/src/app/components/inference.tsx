
export default function Inference() {
  return (
    <div className="bg-secondary rounded-2xl shadow-lg p-8 w-full max-w-lg mx-auto flex flex-col justify-between gap-6 transform transition-transform duration-500 hover:scale-105">
      
      {/* Output Display */}
      <div className="bg-primary rounded-xl p-6 flex-1 text-neutral h-60 overflow-y-auto shadow-inner">
        <p>AI Response will appear here...</p>
      </div>

      {/* Input Area */}
      <div className="flex gap-4 mt-4">
        <input
          type="text"
          placeholder="Type your query..."
          className="flex-1 bg-primary text-neutral rounded-xl px-4 py-3 focus:outline-none focus:ring-2 focus:ring-accent placeholder-neutral placeholder-opacity-60 transition"
        />
        <button className="bg-accent text-primary rounded-xl px-6 py-3 hover:bg-blue-500 transition transform hover:scale-105">
          Chat
        </button>
      </div>
    </div>
  );
}

