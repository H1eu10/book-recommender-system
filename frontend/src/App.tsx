import { useEffect, useState } from 'react'
import { getBooks } from './services/books'
import type { Book } from './types/book'
import RecommendationPanel from './components/RecommendationPanel'
import './App.css'

function App() {
  const [books, setBooks] = useState<Book[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const controller = new AbortController()

    async function loadBooks() {
      try {
        const data = await getBooks(controller.signal)

        if (!controller.signal.aborted) {
          setBooks(data)
        }
      } catch (error: unknown) {
        if (!controller.signal.aborted) {
          setError(
            error instanceof Error
              ? error.message
              : 'Something went wrong while loading books.',
          )
        }
      } finally {
        if (!controller.signal.aborted) {
          setLoading(false)
        }
      }
    }

    void loadBooks()

    return () => {
      controller.abort()
    }
  }, [])

  return (
    <main className="app">
      <header className="page-header">
        <p className="eyebrow">Book Recommendation System</p>
        <h1>Explore the library</h1>
        <p>
          Explore the collection and discover books that match your preferences.
        </p>
      </header>

      {loading && <p role="status">Loading books...</p>}

      {!loading && error && (
        <div className="error-message" role="alert">
          <p>{error}</p>
          <button
            type="button"
            onClick={() => window.location.reload()}
          >
            Try again
          </button>
        </div>
      )}

      {!loading && !error && books.length === 0 && (
        <p>No books are available yet.</p>
      )}

      {!loading && !error && books.length > 0 && (
        <>
          <RecommendationPanel books={books} />
          <h2 className="library-heading">Library collection</h2>
          <p className="result-count">
            {books.length} books available
          </p>

          <section className="book-grid" aria-label="Book collection">
            {books.map((book) => (
              <article className="book-card" key={book.id}>
                <div className="genre-list">
                  {book.genres.map((genre) => (
                    <span className="genre" key={genre}>
                      {genre}
                    </span>
                  ))}
                </div>

                <h2>{book.title}</h2>
                <p className="book-author">by {book.author}</p>
                <p className="book-description">{book.description}</p>

                <p className="book-meta">
                  {book.language.toUpperCase()} ·{' '}
                  {book.pages === null
                    ? 'Page count unavailable'
                    : `${book.pages} pages`}
                </p>
              </article>
            ))}
          </section>
        </>
      )}
    </main>
  )
}

export default App