interface Props {
  id: string
  title: string
  author: string
}

function getCoverVariant(id: string): number {
  let hash = 0

  for (const character of id) {
    hash = (hash * 31 + character.charCodeAt(0)) >>> 0
  }

  return hash % 5
}

export default function BookCover({ id, title, author }: Props) {
  const variant = getCoverVariant(id)

  return (
    <div className="book-cover-stage" aria-hidden="true">
      <div className={`book-cover book-cover--${variant}`}>
        <div className="book-cover__frame">
          <span className="book-cover__ornament">✦</span>

          <span className="book-cover__title">
            {title}
          </span>

          <span className="book-cover__divider" />

          <span className="book-cover__author">
            {author}
          </span>
        </div>
      </div>
    </div>
  )
}