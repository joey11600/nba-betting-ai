/**
 * NBA Player Autocomplete Search for Base44
 * Drop this JavaScript into your Base44 app
 */

class NBAPlayerSearch {
    constructor(config = {}) {
        this.apiBaseUrl = config.apiBaseUrl || 'http://localhost:5000/api';
        this.inputElement = config.inputElement;
        this.resultsElement = config.resultsElement;
        this.onSelect = config.onSelect || ((player) => console.log('Selected:', player));
        this.debounceDelay = config.debounceDelay || 300;
        this.minChars = config.minChars || 2;
        
        this.debounceTimer = null;
        this.selectedPlayer = null;
        
        this.init();
    }
    
    init() {
        if (!this.inputElement || !this.resultsElement) {
            console.error('NBAPlayerSearch: Missing input or results element');
            return;
        }
        
        // Setup event listeners
        this.inputElement.addEventListener('input', (e) => this.handleInput(e));
        this.inputElement.addEventListener('keydown', (e) => this.handleKeyboard(e));
        
        // Click outside to close
        document.addEventListener('click', (e) => {
            if (!this.inputElement.contains(e.target) && !this.resultsElement.contains(e.target)) {
                this.hideResults();
            }
        });
        
        // Style results container
        this.resultsElement.style.cssText = `
            position: absolute;
            background: white;
            border: 1px solid #ddd;
            border-radius: 4px;
            max-height: 300px;
            overflow-y: auto;
            display: none;
            z-index: 1000;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            width: ${this.inputElement.offsetWidth}px;
        `;
    }
    
    handleInput(event) {
        const query = event.target.value.trim();
        
        clearTimeout(this.debounceTimer);
        
        if (query.length < this.minChars) {
            this.hideResults();
            return;
        }
        
        // Debounce API calls
        this.debounceTimer = setTimeout(() => {
            this.searchPlayers(query);
        }, this.debounceDelay);
    }
    
    async searchPlayers(query) {
        try {
            const response = await fetch(
                `${this.apiBaseUrl}/players/search?q=${encodeURIComponent(query)}&limit=10`
            );
            
            if (!response.ok) {
                throw new Error('Search failed');
            }
            
            const data = await response.json();
            
            if (data.success && data.players.length > 0) {
                this.displayResults(data.players);
            } else {
                this.showNoResults();
            }
            
        } catch (error) {
            console.error('Player search error:', error);
            this.showError();
        }
    }
    
    displayResults(players) {
        this.resultsElement.innerHTML = '';
        
        players.forEach((player, index) => {
            const item = document.createElement('div');
            item.className = 'player-result-item';
            item.dataset.index = index;
            item.dataset.playerId = player.player_id;
            item.dataset.playerName = player.full_name;
            
            item.style.cssText = `
                padding: 12px 15px;
                cursor: pointer;
                border-bottom: 1px solid #f0f0f0;
                transition: background-color 0.2s;
            `;
            
            item.innerHTML = `
                <div style="font-weight: 600; color: #1a1a2e;">${player.full_name}</div>
                <div style="font-size: 12px; color: #666; margin-top: 2px;">ID: ${player.player_id}</div>
            `;
            
            // Hover effect
            item.addEventListener('mouseenter', () => {
                item.style.backgroundColor = '#f5f5f5';
            });
            
            item.addEventListener('mouseleave', () => {
                item.style.backgroundColor = 'white';
            });
            
            // Click handler
            item.addEventListener('click', () => {
                this.selectPlayer(player);
            });
            
            this.resultsElement.appendChild(item);
        });
        
        this.showResults();
    }
    
    selectPlayer(player) {
        this.selectedPlayer = player;
        this.inputElement.value = player.full_name;
        this.hideResults();
        this.onSelect(player);
    }
    
    showResults() {
        this.resultsElement.style.display = 'block';
    }
    
    hideResults() {
        this.resultsElement.style.display = 'none';
    }
    
    showNoResults() {
        this.resultsElement.innerHTML = `
            <div style="padding: 15px; text-align: center; color: #666;">
                No players found
            </div>
        `;
        this.showResults();
    }
    
    showError() {
        this.resultsElement.innerHTML = `
            <div style="padding: 15px; text-align: center; color: #e94560;">
                Error searching players
            </div>
        `;
        this.showResults();
    }
    
    handleKeyboard(event) {
        const items = this.resultsElement.querySelectorAll('.player-result-item');
        
        if (items.length === 0) return;
        
        const activeItem = this.resultsElement.querySelector('.active');
        let activeIndex = activeItem ? parseInt(activeItem.dataset.index) : -1;
        
        switch (event.key) {
            case 'ArrowDown':
                event.preventDefault();
                activeIndex = (activeIndex + 1) % items.length;
                this.setActiveItem(items, activeIndex);
                break;
                
            case 'ArrowUp':
                event.preventDefault();
                activeIndex = activeIndex <= 0 ? items.length - 1 : activeIndex - 1;
                this.setActiveItem(items, activeIndex);
                break;
                
            case 'Enter':
                event.preventDefault();
                if (activeIndex >= 0) {
                    const item = items[activeIndex];
                    this.selectPlayer({
                        player_id: parseInt(item.dataset.playerId),
                        full_name: item.dataset.playerName
                    });
                }
                break;
                
            case 'Escape':
                this.hideResults();
                break;
        }
    }
    
    setActiveItem(items, index) {
        items.forEach(item => {
            item.classList.remove('active');
            item.style.backgroundColor = 'white';
        });
        
        if (index >= 0 && index < items.length) {
            items[index].classList.add('active');
            items[index].style.backgroundColor = '#f5f5f5';
            items[index].scrollIntoView({ block: 'nearest' });
        }
    }
    
    getSelectedPlayer() {
        return this.selectedPlayer;
    }
    
    clear() {
        this.inputElement.value = '';
        this.selectedPlayer = null;
        this.hideResults();
    }
}


// ======================
// BASE44 INTEGRATION HELPER
// ======================

/**
 * Initialize player search in Base44
 * Call this from your Base44 JavaScript
 */
function initNBAPlayerSearch(inputId, resultsId, callback) {
    const inputElement = document.getElementById(inputId);
    const resultsElement = document.getElementById(resultsId);
    
    if (!inputElement || !resultsElement) {
        console.error('NBA Player Search: Elements not found');
        return null;
    }
    
    return new NBAPlayerSearch({
        apiBaseUrl: 'http://localhost:5000/api',  // Change to your deployed API
        inputElement: inputElement,
        resultsElement: resultsElement,
        onSelect: callback || function(player) {
            console.log('Selected player:', player);
            // Store player data for Base44 form
            document.getElementById('selected_player_id').value = player.player_id;
            document.getElementById('selected_player_name').value = player.full_name;
        }
    });
}


// ======================
// EXAMPLE HTML FOR BASE44
// ======================

/*
<!-- Add this HTML to your Base44 form -->

<div style="position: relative; margin-bottom: 20px;">
    <label for="player_search" style="display: block; margin-bottom: 5px; font-weight: 600;">
        Search Player
    </label>
    
    <input 
        type="text" 
        id="player_search" 
        placeholder="Type player name (e.g., Jaden Ivey)"
        style="width: 100%; padding: 10px; border: 1px solid #ddd; border-radius: 4px; font-size: 14px;"
    />
    
    <div id="player_results"></div>
    
    <!-- Hidden fields to store selected player -->
    <input type="hidden" id="selected_player_id" name="player_id" />
    <input type="hidden" id="selected_player_name" name="player_name" />
</div>

<!-- Initialize the search -->
<script>
    // Initialize when page loads
    window.addEventListener('DOMContentLoaded', function() {
        initNBAPlayerSearch('player_search', 'player_results', function(player) {
            console.log('Player selected:', player);
            
            // Store in Base44 variables or form fields
            document.getElementById('selected_player_id').value = player.player_id;
            document.getElementById('selected_player_name').value = player.full_name;
            
            // You can trigger Base44 workflows here
            alert(`Selected: ${player.full_name} (ID: ${player.player_id})`);
        });
    });
</script>
*/
