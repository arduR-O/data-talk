
// UploadCard.jsx
export default function UploadCard() {
  return (
    <div className="bg-secondary rounded-2xl shadow-lg p-6 w-full max-w-md mx-auto space-y-4">
      <h2 className="text-accent text-lg font-semibold">Upload & Connect</h2>

      {/* PDF Upload */}
      <div className="bg-primary rounded-xl p-4 flex flex-col items-center justify-center border-2 border-dashed border-accent h-32">
        <p className="text-neutral mb-2">Drag & Drop PDF here</p>
        <button className="bg-accent text-primary px-4 py-2 rounded-xl hover:bg-blue-500 transition">
          Browse Files
        </button>
      </div>

      {/* Database URL Input */}
      <input
        type="text"
        placeholder="Enter Database URL"
        className="w-full bg-primary text-neutral rounded-xl px-4 py-2 focus:outline-none focus:ring-2 focus:ring-accent"
      />

      {/* API Key Input */}
      <input
        type="text"
        placeholder="Enter API Key"
        className="w-full bg-primary text-neutral rounded-xl px-4 py-2 focus:outline-none focus:ring-2 focus:ring-accent"
      />

      {/* Submit Button */}
      <button className="bg-success text-primary w-full py-2 rounded-xl hover:bg-green-600 transition">
        Connect
      </button>
    </div>
  );
}


