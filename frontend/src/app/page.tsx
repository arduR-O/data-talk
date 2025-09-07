import Inference from "./components/inference";
import UploadCard from "./components/Upload";

export default function Home() {
  return (
    <main className="bg-slate-900 min-h-screen flex flex-col items-center py-8 px-4 md:px-16">
      
      {/* Title with animation */}
      <div className="text-center mb-12">
        <h1 className="font-mono text-w text-3xl md:text-5xl font-bold mb-4 animate-pulse">
          DataTalk
        </h1>
        <p className="text-gray-600 text-lg md:text-xl max-w-2xl mx-auto">
          Your AI Data Scientist - Upload documents, connect data sources, and have intelligent conversations
        </p>
      </div>
      
      {/* Cards container */}
      <div className="flex flex-col xl:flex-row gap-8 w-full max-w-7xl justify-center items-start">
        {/* Upload Card */}
        <div className="w-full xl:w-auto flex justify-center">
          <UploadCard />
        </div>
        
        {/* Inference Card */}
        <div className="w-full xl:w-auto flex justify-center">
          <Inference />
        </div>
      </div>
    </main>
  )
}