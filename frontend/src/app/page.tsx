import Inference from "./components/inference";
import UploadCard from "./components/Upload";

export default function Home() {
  return (
    <main className="bg-slate-900 min-h-screen flex flex-col items-center py-4 sm:py-8 px-4 sm:px-8 md:px-16">
      
      {/* Title with animation */}
      <div className="text-center mb-6 sm:mb-12">
        <h1 className="font-mono text-white text-2xl sm:text-3xl md:text-5xl font-bold mb-4 animate-pulse flex flex-col sm:flex-row items-center justify-center gap-4">
          <img 
            src="/db-icon.svg" 
            alt="Database Icon" 
            className="w-24 h-24 sm:w-32 sm:h-32 md:w-40 md:h-40 text-blue-400"
          />
          <span>DataTalk</span>
        </h1>
        <p className="text-gray-600 text-base sm:text-lg md:text-xl max-w-2xl mx-auto px-4">
          Your AI Data Scientist - Upload documents, connect data sources, and have intelligent conversations
        </p>
      </div>
      
      {/* Cards container */}
      <div className="flex flex-col lg:flex-row gap-6 lg:gap-8 w-full max-w-7xl justify-center items-stretch">
        {/* Upload Card */}
        <div className="w-full lg:w-auto flex justify-center">
          <UploadCard />
        </div>
        
        {/* Inference Card */}
        <div className="w-full lg:w-auto flex justify-center">
          <Inference />
        </div>
      </div>
    </main>
  )
}