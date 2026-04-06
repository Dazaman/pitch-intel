import SearchBar from "@/components/search-bar";

export default function Home() {
  return (
    <div className="flex flex-col items-center pt-20">
      <h1 className="text-4xl font-bold mb-2">Pitch Intel</h1>
      <p className="text-gray-400 mb-8">
        Football intelligence — player and team analytics
      </p>
      <SearchBar />
    </div>
  );
}
