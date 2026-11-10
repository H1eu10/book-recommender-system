import { useEffect, useRef } from 'react'
import type { CSSProperties, ReactNode } from 'react'

interface Props {
  children: ReactNode
  index: number
}

export default function BookFade({ children, index }: Props) {
  const elementRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    const element = elementRef.current

    if (!element || !('IntersectionObserver' in window)) {
      return
    }

    const motionPreference = window.matchMedia(
      '(prefers-reduced-motion: reduce)',
    )

    if (motionPreference.matches) {
      return
    }

    const observer = new IntersectionObserver(
      entries => {
        if (entries.some(entry => entry.isIntersecting)) {
          element.classList.remove('book-fade--pending')
          observer.disconnect()
        }
      },
      {
        threshold: 0,
        rootMargin: '0px 0px -24px 0px',
      },
    )

    function showImmediately() {
      element?.classList.add('book-fade--instant')
      element?.classList.remove('book-fade--pending')
      observer.disconnect()
    }

    function handleMotionChange(event: MediaQueryListEvent) {
      if (event.matches) {
        showImmediately()
      }
    }

    element.classList.add('book-fade--pending')
    observer.observe(element)

    element.addEventListener('focusin', showImmediately)
    motionPreference.addEventListener('change', handleMotionChange)

    return () => {
      observer.disconnect()
      element.classList.remove(
        'book-fade--pending',
        'book-fade--instant',
      )

      element.removeEventListener('focusin', showImmediately)
      motionPreference.removeEventListener(
        'change',
        handleMotionChange,
      )
    }
  }, [])

  const style: CSSProperties = {
    transitionDelay: `${(index % 3) * 100}ms`,
  }

  return (
    <div
      ref={elementRef}
      className="book-fade"
      style={style}
    >
      {children}
    </div>
  )
}