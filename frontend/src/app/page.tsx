import Inference from "./components/inference";
import UploadCard from "./components/Upload"

export default function Home() {
  return (
    <main className="bg-primary min-h-screen flex flex-col items-center py-8 px-4 md:px-16">
      
      {/* Title with animation */}
      <p className="font-mono text-center text-neutral text-2xl md:text-4xl mb-8   p-4 rounded-lg animate-pulse">
        DataTalk: Your AI Data Scientist
      </p>
      
      {/* Cards container */}
      <div className="flex flex-col md:flex-row gap-6 w-full md:w-auto justify-center items-stretch">
       
        
        {/* Upload Card */}
        <div className="flex-1 bg-secondary rounded-2xl shadow-lg p-6 transform transition-transform duration-500 hover:scale-105 hover:shadow-2xl animate-fadeIn">
          <UploadCard />
        </div>
         {/* Inference Card */}
        <div className="flex-1 bg-secondary rounded-2xl shadow-lg p-6 transform transition-transform duration-500 hover:scale-105 hover:shadow-2xl animate-fadeIn">
          <Inference />
        </div>
      </div>
    </main>
  )
}

