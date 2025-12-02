import React, { useState, useEffect, useRef } from 'react';

/**
 * NBA Player Search Component (React)
 * For Base44 apps that support React components
 */

const NBAPlayerSearch = ({ 
  apiBaseUrl = 'http://localhost:5000/api',
  onSelect,
  placeholder = 'Search NBA player...',
  minChars = 2,
  debounceDelay = 300 
}) => {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [showResults, setShowResults] = useState(false);
  const [selectedPlayer, setSelectedPlayer] = useState(null);
  const [activeIndex, setActiveIndex] = useState(-1);
  
  const inputRef = useRef(null);
  const resultsRef = useRef(null);
  const debounceTimer = useRef(null);

  // Search for players
  const searchPlayers = async (searchQuery) => {
    if (searchQuery.length < minChars) {
      setResults([]);
      setShowResults(false);
      return;
    }

    setIsLoading(true);

    try {
      const response = await fetch(
        `${apiBaseUrl}/players/search?q=${encodeURIComponent(searchQuery)}&limit=10`
      );
      
      const data = await response.json();
      
      if (data.success && data.players) {
        setResults(data.players);
        setShowResults(data.players.length > 0);
      } else {
        setResults([]);
        setShowResults(false);
      }
    } catch (error) {
      console.error('Player search error:', error);
      setResults([]);
      setShowResults(false);
    } finally {
      setIsLoading(false);
    }
  };

  // Debounced search
  useEffect(() => {
    if (debounceTimer.current) {
      clearTimeout(debounceTimer.current);
    }

    if (query.trim().length >= minChars) {
      debounceTimer.current = setTimeout(() => {
        searchPlayers(query.trim());
      }, debounceDelay);
    } else {
      setResults([]);
      setShowResults(false);
    }

    return () => {
      if (debounceTimer.current) {
        clearTimeout(debounceTimer.current);
      }
    };
  }, [query]);

  // Handle player selection
  const handleSelect = (player) => {
    setSelectedPlayer(player);
    setQuery(player.full_name);
    setShowResults(false);
    setActiveIndex(-1);
    
    if (onSelect) {
      onSelect(player);
    }
  };

  // Handle keyboard navigation
  const handleKeyDown = (e) => {
    if (!showResults || results.length === 0) return;

    switch (e.key) {
      case 'ArrowDown':
        e.preventDefault();
        setActiveIndex((prev) => 
          prev < results.length - 1 ? prev + 1 : prev
        );
        break;
        
      case 'ArrowUp':
        e.preventDefault();
        setActiveIndex((prev) => (prev > 0 ? prev - 1 : 0));
        break;
        
      case 'Enter':
        e.preventDefault();
        if (activeIndex >= 0 && activeIndex < results.length) {
          handleSelect(results[activeIndex]);
        }
        break;
        
      case 'Escape':
        setShowResults(false);
        setActiveIndex(-1);
        break;
    }
  };

  // Click outside to close
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (
        inputRef.current &&
        !inputRef.current.contains(event.target) &&
        resultsRef.current &&
        !resultsRef.current.contains(event.target)
      ) {
        setShowResults(false);
        setActiveIndex(-1);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, []);

  return (
    <div style={{ position: 'relative', width: '100%' }}>
      <input
        ref={inputRef}
        type="text"
        value={query}
        onChange={(e) => setQuery(e.target.value)}
        onKeyDown={handleKeyDown}
        placeholder={placeholder}
        style={{
          width: '100%',
          padding: '12px 15px',
          border: '1px solid #ddd',
          borderRadius: '6px',
          fontSize: '14px',
          outline: 'none',
          transition: 'border-color 0.2s',
          boxSizing: 'border-box'
        }}
        onFocus={() => {
          if (results.length > 0) {
            setShowResults(true);
          }
        }}
      />

      {showResults && (
        <div
          ref={resultsRef}
          style={{
            position: 'absolute',
            top: '100%',
            left: 0,
            right: 0,
            marginTop: '4px',
            backgroundColor: 'white',
            border: '1px solid #ddd',
            borderRadius: '6px',
            boxShadow: '0 4px 12px rgba(0, 0, 0, 0.15)',
            maxHeight: '300px',
            overflowY: 'auto',
            zIndex: 1000
          }}
        >
          {isLoading ? (
            <div style={{ padding: '15px', textAlign: 'center', color: '#666' }}>
              Loading...
            </div>
          ) : results.length > 0 ? (
            results.map((player, index) => (
              <div
                key={player.player_id}
                onClick={() => handleSelect(player)}
                onMouseEnter={() => setActiveIndex(index)}
                style={{
                  padding: '12px 15px',
                  cursor: 'pointer',
                  borderBottom: index < results.length - 1 ? '1px solid #f0f0f0' : 'none',
                  backgroundColor: activeIndex === index ? '#f5f5f5' : 'white',
                  transition: 'background-color 0.15s'
                }}
              >
                <div style={{ fontWeight: 600, color: '#1a1a2e', marginBottom: '2px' }}>
                  {player.full_name}
                </div>
                <div style={{ fontSize: '12px', color: '#666' }}>
                  ID: {player.player_id}
                </div>
              </div>
            ))
          ) : (
            <div style={{ padding: '15px', textAlign: 'center', color: '#666' }}>
              No players found
            </div>
          )}
        </div>
      )}

      {selectedPlayer && (
        <input
          type="hidden"
          name="selected_player_id"
          value={selectedPlayer.player_id}
        />
      )}
    </div>
  );
};

export default NBAPlayerSearch;


/**
 * USAGE EXAMPLE IN BASE44:
 * 
 * import NBAPlayerSearch from './NBAPlayerSearch';
 * 
 * function MyBettingForm() {
 *   const [selectedPlayer, setSelectedPlayer] = useState(null);
 * 
 *   return (
 *     <div>
 *       <label>Search Player</label>
 *       <NBAPlayerSearch 
 *         apiBaseUrl="http://localhost:5000/api"
 *         onSelect={(player) => {
 *           setSelectedPlayer(player);
 *           console.log('Selected:', player);
 *         }}
 *         placeholder="Type player name..."
 *       />
 *       
 *       {selectedPlayer && (
 *         <div>
 *           Selected: {selectedPlayer.full_name} (ID: {selectedPlayer.player_id})
 *         </div>
 *       )}
 *     </div>
 *   );
 * }
 */
