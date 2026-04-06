"use client";

import { useRouter } from "next/navigation";
import { useEffect, useRef, useState } from "react";
import { searchPlayers, type PersonSummary, type TeamSummary } from "@/lib/api";

export default function SearchBar() {
  const [query, setQuery] = useState("");
  const [type, setType] = useState<"player" | "team">("player");
  const [results, setResults] = useState<(PersonSummary | TeamSummary)[]>([]);
  const [isOpen, setIsOpen] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const router = useRouter();
  const timeoutRef = useRef<NodeJS.Timeout | null>(null);

  useEffect(() => {
    if (query.length < 2) {
      setResults([]);
      setIsOpen(false);
      return;
    }

    if (timeoutRef.current) clearTimeout(timeoutRef.current);

    timeoutRef.current = setTimeout(async () => {
      setIsLoading(true);
      try {
        const data = await searchPlayers(query, type);
        setResults(data.results);
        setIsOpen(true);
      } catch {
        setResults([]);
      } finally {
        setIsLoading(false);
      }
    }, 300);

    return () => {
      if (timeoutRef.current) clearTimeout(timeoutRef.current);
    };
  }, [query, type]);

  function handleSelect(item: PersonSummary | TeamSummary) {
    setIsOpen(false);
    setQuery("");
    if ("type" in item && (item as PersonSummary).type) {
      router.push(`/player/${item.reep_id}`);
    } else {
      router.push(`/team/${item.reep_id}`);
    }
  }

  return (
    <div className="relative w-full max-w-xl">
      <div className="flex gap-2 mb-2">
        <button
          onClick={() => setType("player")}
          className={`px-3 py-1 rounded text-sm font-medium transition-colors ${
            type === "player"
              ? "bg-blue-600 text-white"
              : "bg-gray-800 text-gray-400 hover:text-gray-200"
          }`}
        >
          Players
        </button>
        <button
          onClick={() => setType("team")}
          className={`px-3 py-1 rounded text-sm font-medium transition-colors ${
            type === "team"
              ? "bg-blue-600 text-white"
              : "bg-gray-800 text-gray-400 hover:text-gray-200"
          }`}
        >
          Teams
        </button>
      </div>

      <input
        type="text"
        value={query}
        onChange={(e) => setQuery(e.target.value)}
        placeholder={`Search ${type}s...`}
        className="w-full rounded-lg border border-gray-600 bg-gray-800 px-4 py-3 text-lg text-white placeholder-gray-400 focus:border-blue-500 focus:outline-none"
      />

      {isLoading && (
        <div className="absolute right-3 top-[52px] text-gray-500 text-sm">Loading...</div>
      )}

      {isOpen && results.length > 0 && (
        <ul className="absolute z-10 mt-1 w-full rounded-lg border border-gray-600 bg-gray-800 shadow-lg max-h-80 overflow-y-auto">
          {results.map((item) => (
            <li key={item.reep_id}>
              <button
                onClick={() => handleSelect(item)}
                className="w-full px-4 py-3 text-left hover:bg-gray-700 flex justify-between items-center"
              >
                <span className="font-medium">{item.name}</span>
                {"position" in item && item.position && (
                  <span className="text-sm text-gray-500">{item.position}</span>
                )}
                {"country" in item && item.country && (
                  <span className="text-sm text-gray-500">{item.country}</span>
                )}
              </button>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
