import { useEffect, useRef } from 'react'
import type { ReactNode } from 'react'

interface Props {
  children: ReactNode
}

export default function ScrollReveal({ children }: Props) {
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
          element.classList.remove('scroll-reveal--pending')
          observer.disconnect()
        }
      },
      {
        threshold: 0,
        rootMargin: '0px 0px -32px 0px',
      },
    )

    function showContent() {
      element?.classList.remove('scroll-reveal--pending')
      observer.disconnect()
    }

    function handleMotionChange(event: MediaQueryListEvent) {
      if (event.matches) {
        showContent()
      }
    }

    const bounds = element.getBoundingClientRect()
    const isAlreadyVisible =
      bounds.top < window.innerHeight && bounds.bottom > 0

    if (!isAlreadyVisible) {
      element.classList.add('scroll-reveal--pending')
      observer.observe(element)
    }

    element.addEventListener('focusin', showContent)
    motionPreference.addEventListener('change', handleMotionChange)

    return () => {
      observer.disconnect()
      element.classList.remove('scroll-reveal--pending')
      element.removeEventListener('focusin', showContent)
      motionPreference.removeEventListener('change', handleMotionChange)
    }
  }, [])

  return (
    <div ref={elementRef} className="scroll-reveal">
      {children}
    </div>
  )
}