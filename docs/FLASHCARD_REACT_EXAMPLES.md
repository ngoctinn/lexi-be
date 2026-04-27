# Flashcard System - React Component Examples

## Table of Contents

1. [Custom Hooks](#custom-hooks)
2. [Components](#components)
3. [Complete Example App](#complete-example-app)
4. [State Management](#state-management)

---

## Custom Hooks

### useFlashcards Hook

```typescript
import { useState, useCallback } from 'react';

interface Flashcard {
  flashcard_id: string;
  word: string;
  translation_vi: string;
  phonetic: string;
  audio_url: string;
  example_sentence: string;
  ease_factor: number;
  repetition_count: number;
  interval_days: number;
  review_count: number;
  last_reviewed_at: string;
  next_review_at: string;
}

interface UseFlashcardsReturn {
  cards: Flashcard[];
  loading: boolean;
  error: string | null;
  fetchCards: (filters?: any) => Promise<void>;
  createCard: (card: Partial<Flashcard>) => Promise<Flashcard>;
  updateCard: (id: string, updates: Partial<Flashcard>) => Promise<Flashcard>;
  deleteCard: (id: string) => Promise<void>;
  reviewCard: (id: string, rating: string) => Promise<Flashcard>;
}

export function useFlashcards(): UseFlashcardsReturn {
  const [cards, setCards] = useState<Flashcard[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const token = localStorage.getItem('token');
  const baseUrl = process.env.REACT_APP_API_URL || 'https://api.example.com';

  const fetchCards = useCallback(async (filters?: any) => {
    setLoading(true);
    setError(null);
    try {
      const url = new URL(`${baseUrl}/flashcards`);
      if (filters?.word_prefix) {
        url.searchParams.append('word_prefix', filters.word_prefix);
      }
      if (filters?.maturity_level) {
        url.searchParams.append('maturity_level', filters.maturity_level);
      }
      if (filters?.min_interval !== undefined) {
        url.searchParams.append('min_interval', filters.min_interval);
      }
      if (filters?.max_interval !== undefined) {
        url.searchParams.append('max_interval', filters.max_interval);
      }
      if (filters?.limit) {
        url.searchParams.append('limit', filters.limit);
      }
      if (filters?.cursor) {
        url.searchParams.append('cursor', filters.cursor);
      }

      const response = await fetch(url.toString(), {
        headers: { 'Authorization': `Bearer ${token}` }
      });

      if (!response.ok) {
        throw new Error(`Failed to fetch: ${response.statusText}`);
      }

      const data = await response.json();
      setCards(data.data.flashcards);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
    } finally {
      setLoading(false);
    }
  }, [token, baseUrl]);

  const createCard = useCallback(async (card: Partial<Flashcard>) => {
    try {
      const response = await fetch(`${baseUrl}/flashcards`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(card)
      });

      if (!response.ok) {
        throw new Error(`Failed to create: ${response.statusText}`);
      }

      const data = await response.json();
      setCards([...cards, data.data]);
      return data.data;
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
      throw err;
    }
  }, [token, baseUrl, cards]);

  const updateCard = useCallback(async (id: string, updates: Partial<Flashcard>) => {
    try {
      const response = await fetch(`${baseUrl}/flashcards/${id}`, {
        method: 'PATCH',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(updates)
      });

      if (!response.ok) {
        throw new Error(`Failed to update: ${response.statusText}`);
      }

      const data = await response.json();
      setCards(cards.map(c => c.flashcard_id === id ? data.data : c));
      return data.data;
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
      throw err;
    }
  }, [token, baseUrl, cards]);

  const deleteCard = useCallback(async (id: string) => {
    try {
      const response = await fetch(`${baseUrl}/flashcards/${id}`, {
        method: 'DELETE',
        headers: { 'Authorization': `Bearer ${token}` }
      });

      if (!response.ok) {
        throw new Error(`Failed to delete: ${response.statusText}`);
      }

      setCards(cards.filter(c => c.flashcard_id !== id));
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
      throw err;
    }
  }, [token, baseUrl, cards]);

  const reviewCard = useCallback(async (id: string, rating: string) => {
    try {
      const response = await fetch(`${baseUrl}/flashcards/${id}/review`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ rating })
      });

      if (!response.ok) {
        throw new Error(`Failed to review: ${response.statusText}`);
      }

      const data = await response.json();
      setCards(cards.map(c => c.flashcard_id === id ? data.data : c));
      return data.data;
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
      throw err;
    }
  }, [token, baseUrl, cards]);

  return {
    cards,
    loading,
    error,
    fetchCards,
    createCard,
    updateCard,
    deleteCard,
    reviewCard
  };
}
```

### useStatistics Hook

```typescript
import { useState, useCallback, useEffect } from 'react';

interface Statistics {
  total_count: number;
  due_today: number;
  reviewed_last_7_days: number;
  maturity: {
    new: number;
    learning: number;
    mature: number;
  };
  average_ease_factor: number;
}

export function useStatistics() {
  const [stats, setStats] = useState<Statistics | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const token = localStorage.getItem('token');
  const baseUrl = process.env.REACT_APP_API_URL || 'https://api.example.com';

  const fetchStatistics = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await fetch(`${baseUrl}/flashcards/statistics`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });

      if (!response.ok) {
        throw new Error(`Failed to fetch statistics: ${response.statusText}`);
      }

      const data = await response.json();
      setStats(data.data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
    } finally {
      setLoading(false);
    }
  }, [token, baseUrl]);

  useEffect(() => {
    fetchStatistics();
  }, [fetchStatistics]);

  return { stats, loading, error, refetch: fetchStatistics };
}
```

---

## Components

### FlashcardCard Component

```typescript
import React from 'react';
import './FlashcardCard.css';

interface FlashcardCardProps {
  card: Flashcard;
  onReview: (rating: string) => void;
  onEdit: () => void;
  onDelete: () => void;
  loading?: boolean;
}

export function FlashcardCard({
  card,
  onReview,
  onEdit,
  onDelete,
  loading = false
}: FlashcardCardProps) {
  const [flipped, setFlipped] = React.useState(false);

  const getMaturityLabel = () => {
    if (card.repetition_count === 0) return 'New';
    if (card.repetition_count <= 2) return 'Learning';
    return 'Mature';
  };

  const getMaturityColor = () => {
    if (card.repetition_count === 0) return '#3498db'; // blue
    if (card.repetition_count <= 2) return '#f39c12'; // orange
    return '#27ae60'; // green
  };

  return (
    <div className="flashcard-card">
      <div className="card-header">
        <span className="maturity-badge" style={{ backgroundColor: getMaturityColor() }}>
          {getMaturityLabel()}
        </span>
        <span className="ease-factor">Ease: {card.ease_factor.toFixed(2)}</span>
      </div>

      <div
        className={`card-content ${flipped ? 'flipped' : ''}`}
        onClick={() => setFlipped(!flipped)}
      >
        {!flipped ? (
          <div className="front">
            <div className="word">{card.word}</div>
            <div className="phonetic">{card.phonetic}</div>
            {card.audio_url && (
              <audio controls className="audio">
                <source src={card.audio_url} type="audio/mpeg" />
              </audio>
            )}
            <div className="hint">Click to reveal translation</div>
          </div>
        ) : (
          <div className="back">
            <div className="translation">{card.translation_vi}</div>
            <div className="example">{card.example_sentence}</div>
            <div className="hint">Click to see word</div>
          </div>
        )}
      </div>

      <div className="card-stats">
        <div className="stat">
          <span className="label">Reviews:</span>
          <span className="value">{card.review_count}</span>
        </div>
        <div className="stat">
          <span className="label">Next Review:</span>
          <span className="value">{card.interval_days} days</span>
        </div>
      </div>

      <div className="card-actions">
        <button
          className="btn btn-forgot"
          onClick={() => onReview('forgot')}
          disabled={loading}
        >
          Forgot
        </button>
        <button
          className="btn btn-hard"
          onClick={() => onReview('hard')}
          disabled={loading}
        >
          Hard
        </button>
        <button
          className="btn btn-good"
          onClick={() => onReview('good')}
          disabled={loading}
        >
          Good
        </button>
        <button
          className="btn btn-easy"
          onClick={() => onReview('easy')}
          disabled={loading}
        >
          Easy
        </button>
      </div>

      <div className="card-footer">
        <button className="btn-icon" onClick={onEdit} title="Edit">
          ✏️
        </button>
        <button className="btn-icon" onClick={onDelete} title="Delete">
          🗑️
        </button>
      </div>
    </div>
  );
}
```

### StatisticsDashboard Component

```typescript
import React from 'react';
import { useStatistics } from '../hooks/useStatistics';
import './StatisticsDashboard.css';

export function StatisticsDashboard() {
  const { stats, loading, error } = useStatistics();

  if (loading) return <div className="loading">Loading statistics...</div>;
  if (error) return <div className="error">Error: {error}</div>;
  if (!stats) return <div className="empty">No statistics available</div>;

  return (
    <div className="statistics-dashboard">
      <div className="stat-card">
        <div className="stat-label">Total Cards</div>
        <div className="stat-value">{stats.total_count}</div>
      </div>

      <div className="stat-card highlight">
        <div className="stat-label">Due Today</div>
        <div className="stat-value">{stats.due_today}</div>
      </div>

      <div className="stat-card">
        <div className="stat-label">Reviewed (7 days)</div>
        <div className="stat-value">{stats.reviewed_last_7_days}</div>
      </div>

      <div className="stat-card">
        <div className="stat-label">New</div>
        <div className="stat-value">{stats.maturity.new}</div>
      </div>

      <div className="stat-card">
        <div className="stat-label">Learning</div>
        <div className="stat-value">{stats.maturity.learning}</div>
      </div>

      <div className="stat-card">
        <div className="stat-label">Mature</div>
        <div className="stat-value">{stats.maturity.mature}</div>
      </div>

      <div className="stat-card">
        <div className="stat-label">Avg Ease Factor</div>
        <div className="stat-value">{stats.average_ease_factor.toFixed(2)}</div>
      </div>
    </div>
  );
}
```

### SearchFilter Component

```typescript
import React, { useState } from 'react';
import './SearchFilter.css';

interface SearchFilterProps {
  onSearch: (filters: any) => void;
  loading?: boolean;
}

export function SearchFilter({ onSearch, loading = false }: SearchFilterProps) {
  const [wordPrefix, setWordPrefix] = useState('');
  const [maturityLevel, setMaturityLevel] = useState('');
  const [minInterval, setMinInterval] = useState('');
  const [maxInterval, setMaxInterval] = useState('');

  const handleSearch = () => {
    onSearch({
      word_prefix: wordPrefix || undefined,
      maturity_level: maturityLevel || undefined,
      min_interval: minInterval ? parseInt(minInterval) : undefined,
      max_interval: maxInterval ? parseInt(maxInterval) : undefined
    });
  };

  const handleReset = () => {
    setWordPrefix('');
    setMaturityLevel('');
    setMinInterval('');
    setMaxInterval('');
    onSearch({});
  };

  return (
    <div className="search-filter">
      <div className="filter-group">
        <label>Word Prefix</label>
        <input
          type="text"
          placeholder="e.g., 'app'"
          value={wordPrefix}
          onChange={(e) => setWordPrefix(e.target.value)}
          disabled={loading}
        />
      </div>

      <div className="filter-group">
        <label>Maturity Level</label>
        <select
          value={maturityLevel}
          onChange={(e) => setMaturityLevel(e.target.value)}
          disabled={loading}
        >
          <option value="">All Levels</option>
          <option value="new">New</option>
          <option value="learning">Learning</option>
          <option value="mature">Mature</option>
        </select>
      </div>

      <div className="filter-group">
        <label>Min Interval (days)</label>
        <input
          type="number"
          min="0"
          value={minInterval}
          onChange={(e) => setMinInterval(e.target.value)}
          disabled={loading}
        />
      </div>

      <div className="filter-group">
        <label>Max Interval (days)</label>
        <input
          type="number"
          min="0"
          value={maxInterval}
          onChange={(e) => setMaxInterval(e.target.value)}
          disabled={loading}
        />
      </div>

      <div className="filter-actions">
        <button
          className="btn btn-primary"
          onClick={handleSearch}
          disabled={loading}
        >
          Search
        </button>
        <button
          className="btn btn-secondary"
          onClick={handleReset}
          disabled={loading}
        >
          Reset
        </button>
      </div>
    </div>
  );
}
```

### ImportExport Component

```typescript
import React, { useRef } from 'react';
import './ImportExport.css';

interface ImportExportProps {
  onImport: (file: File) => Promise<void>;
  onExport: () => Promise<void>;
  loading?: boolean;
}

export function ImportExport({ onImport, onExport, loading = false }: ImportExportProps) {
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleFileSelect = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file) {
      try {
        await onImport(file);
        alert('Import successful!');
      } catch (error) {
        alert(`Import failed: ${error instanceof Error ? error.message : 'Unknown error'}`);
      }
    }
  };

  const handleExport = async () => {
    try {
      await onExport();
      alert('Export successful!');
    } catch (error) {
      alert(`Export failed: ${error instanceof Error ? error.message : 'Unknown error'}`);
    }
  };

  return (
    <div className="import-export">
      <button
        className="btn btn-primary"
        onClick={() => fileInputRef.current?.click()}
        disabled={loading}
      >
        📥 Import
      </button>
      <input
        ref={fileInputRef}
        type="file"
        accept=".json"
        onChange={handleFileSelect}
        style={{ display: 'none' }}
      />

      <button
        className="btn btn-primary"
        onClick={handleExport}
        disabled={loading}
      >
        📤 Export
      </button>
    </div>
  );
}
```

---

## Complete Example App

```typescript
import React, { useState, useEffect } from 'react';
import { useFlashcards } from './hooks/useFlashcards';
import { useStatistics } from './hooks/useStatistics';
import { FlashcardCard } from './components/FlashcardCard';
import { StatisticsDashboard } from './components/StatisticsDashboard';
import { SearchFilter } from './components/SearchFilter';
import { ImportExport } from './components/ImportExport';
import './App.css';

function App() {
  const { cards, loading, error, fetchCards, reviewCard, deleteCard } = useFlashcards();
  const [selectedCard, setSelectedCard] = useState<string | null>(null);
  const [reviewLoading, setReviewLoading] = useState(false);

  useEffect(() => {
    fetchCards();
  }, []);

  const handleReview = async (cardId: string, rating: string) => {
    setReviewLoading(true);
    try {
      await reviewCard(cardId, rating);
      setSelectedCard(null);
    } catch (err) {
      alert(`Review failed: ${err instanceof Error ? err.message : 'Unknown error'}`);
    } finally {
      setReviewLoading(false);
    }
  };

  const handleDelete = async (cardId: string) => {
    if (window.confirm('Are you sure you want to delete this flashcard?')) {
      try {
        await deleteCard(cardId);
      } catch (err) {
        alert(`Delete failed: ${err instanceof Error ? err.message : 'Unknown error'}`);
      }
    }
  };

  const handleSearch = async (filters: any) => {
    await fetchCards(filters);
  };

  const handleImport = async (file: File) => {
    const text = await file.text();
    const data = JSON.parse(text);
    const token = localStorage.getItem('token');
    const baseUrl = process.env.REACT_APP_API_URL || 'https://api.example.com';

    const response = await fetch(`${baseUrl}/flashcards/import`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ flashcards: data.flashcards || data })
    });

    if (!response.ok) {
      throw new Error(`Import failed: ${response.statusText}`);
    }

    await fetchCards();
  };

  const handleExport = async () => {
    const token = localStorage.getItem('token');
    const baseUrl = process.env.REACT_APP_API_URL || 'https://api.example.com';

    const response = await fetch(`${baseUrl}/flashcards/export`, {
      headers: { 'Authorization': `Bearer ${token}` }
    });

    if (!response.ok) {
      throw new Error(`Export failed: ${response.statusText}`);
    }

    const data = await response.json();
    const json = JSON.stringify(data.data.flashcards, null, 2);
    const blob = new Blob([json], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `flashcards-${new Date().toISOString()}.json`;
    a.click();
  };

  return (
    <div className="app">
      <header className="app-header">
        <h1>Flashcard Learning System</h1>
      </header>

      <main className="app-main">
        <section className="statistics-section">
          <StatisticsDashboard />
        </section>

        <section className="controls-section">
          <SearchFilter onSearch={handleSearch} loading={loading} />
          <ImportExport onImport={handleImport} onExport={handleExport} loading={loading} />
        </section>

        {error && <div className="error-message">{error}</div>}

        <section className="cards-section">
          {loading ? (
            <div className="loading">Loading flashcards...</div>
          ) : cards.length === 0 ? (
            <div className="empty">No flashcards found</div>
          ) : (
            <div className="cards-grid">
              {cards.map((card) => (
                <FlashcardCard
                  key={card.flashcard_id}
                  card={card}
                  onReview={(rating) => handleReview(card.flashcard_id, rating)}
                  onEdit={() => {/* TODO: Implement edit */}}
                  onDelete={() => handleDelete(card.flashcard_id)}
                  loading={reviewLoading}
                />
              ))}
            </div>
          )}
        </section>
      </main>
    </div>
  );
}

export default App;
```

---

## State Management

### Redux Slice Example

```typescript
import { createSlice, createAsyncThunk } from '@reduxjs/toolkit';

interface FlashcardsState {
  cards: Flashcard[];
  loading: boolean;
  error: string | null;
}

const initialState: FlashcardsState = {
  cards: [],
  loading: false,
  error: null
};

export const fetchFlashcards = createAsyncThunk(
  'flashcards/fetchFlashcards',
  async (filters?: any, { rejectWithValue }) => {
    try {
      const token = localStorage.getItem('token');
      const url = new URL('/flashcards', process.env.REACT_APP_API_URL);
      
      if (filters?.word_prefix) {
        url.searchParams.append('word_prefix', filters.word_prefix);
      }

      const response = await fetch(url.toString(), {
        headers: { 'Authorization': `Bearer ${token}` }
      });

      if (!response.ok) {
        throw new Error(`Failed to fetch: ${response.statusText}`);
      }

      const data = await response.json();
      return data.data.flashcards;
    } catch (error) {
      return rejectWithValue(error instanceof Error ? error.message : 'Unknown error');
    }
  }
);

const flashcardsSlice = createSlice({
  name: 'flashcards',
  initialState,
  reducers: {},
  extraReducers: (builder) => {
    builder
      .addCase(fetchFlashcards.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(fetchFlashcards.fulfilled, (state, action) => {
        state.loading = false;
        state.cards = action.payload;
      })
      .addCase(fetchFlashcards.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload as string;
      });
  }
});

export default flashcardsSlice.reducer;
```

---

## CSS Styling

### FlashcardCard.css

```css
.flashcard-card {
  background: white;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  padding: 16px;
  margin: 8px;
  max-width: 300px;
  transition: transform 0.2s, box-shadow 0.2s;
}

.flashcard-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.maturity-badge {
  color: white;
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 12px;
  font-weight: bold;
}

.ease-factor {
  font-size: 12px;
  color: #666;
}

.card-content {
  min-height: 150px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #f5f5f5;
  border-radius: 4px;
  cursor: pointer;
  margin: 12px 0;
  padding: 16px;
  text-align: center;
}

.front .word {
  font-size: 24px;
  font-weight: bold;
  margin-bottom: 8px;
}

.front .phonetic {
  font-size: 14px;
  color: #666;
  margin-bottom: 8px;
}

.back .translation {
  font-size: 20px;
  font-weight: bold;
  margin-bottom: 8px;
}

.back .example {
  font-size: 12px;
  color: #666;
  font-style: italic;
}

.hint {
  font-size: 10px;
  color: #999;
  margin-top: 8px;
}

.card-stats {
  display: flex;
  justify-content: space-around;
  margin: 12px 0;
  padding: 8px 0;
  border-top: 1px solid #eee;
  border-bottom: 1px solid #eee;
}

.stat {
  display: flex;
  flex-direction: column;
  align-items: center;
}

.stat .label {
  font-size: 12px;
  color: #666;
}

.stat .value {
  font-size: 16px;
  font-weight: bold;
  color: #333;
}

.card-actions {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 8px;
  margin: 12px 0;
}

.btn {
  padding: 8px 12px;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 12px;
  font-weight: bold;
  transition: background-color 0.2s;
}

.btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.btn-forgot {
  background-color: #e74c3c;
  color: white;
}

.btn-forgot:hover:not(:disabled) {
  background-color: #c0392b;
}

.btn-hard {
  background-color: #f39c12;
  color: white;
}

.btn-hard:hover:not(:disabled) {
  background-color: #d68910;
}

.btn-good {
  background-color: #3498db;
  color: white;
}

.btn-good:hover:not(:disabled) {
  background-color: #2980b9;
}

.btn-easy {
  background-color: #27ae60;
  color: white;
}

.btn-easy:hover:not(:disabled) {
  background-color: #229954;
}

.card-footer {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
  padding-top: 8px;
  border-top: 1px solid #eee;
}

.btn-icon {
  background: none;
  border: none;
  font-size: 18px;
  cursor: pointer;
  padding: 4px 8px;
  transition: transform 0.2s;
}

.btn-icon:hover {
  transform: scale(1.2);
}
```

