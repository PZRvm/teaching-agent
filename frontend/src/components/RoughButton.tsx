import type { ButtonHTMLAttributes } from 'react'
import styled from 'styled-components'

type RoughButtonProps = ButtonHTMLAttributes<HTMLButtonElement> & {
  variant?: 'primary' | 'teacher' | 'outline' | 'icon'
}

export default function RoughButton({
  variant = 'primary',
  className,
  children,
  ...rest
}: RoughButtonProps) {
  return (
    <Wrapper
      {...rest}
      type="button"
      className={[`rough-button rough-button-${variant}`, className]
        .filter(Boolean)
        .join(' ')}
    >
      {children}
    </Wrapper>
  )
}

const Wrapper = styled.button`
  padding: 12px 32px;
  border: 2px solid #1a1a1a;
  border-radius: 8px;
  font-weight: 700;
  font-size: 16px;
  box-shadow: 4px 4px 0px 0px #1a1a1a;
  cursor: pointer;
  transition: transform 0.1s ease, box-shadow 0.1s ease;
  font-family: 'Plus Jakarta Sans', system-ui, sans-serif;

  &:focus-visible {
    outline: 2px dashed #1a1a1a;
    outline-offset: 2px;
  }

  &.rough-button-primary {
    background: #2e5cff;
    color: #ffffff;
  }

  &.rough-button-teacher {
    background: #007d5c;
    color: #ffffff;
  }

  &.rough-button-outline {
    background: #ffffff;
    color: #1a1a1a;
  }

  &.rough-button-icon {
    background: transparent;
    color: #1a1c1c;
    padding: 8px;
    border: none;
    box-shadow: none;
    border-radius: 50%;
    font-size: 24px;
  }

  &:hover {
    box-shadow: 6px 6px 0px 0px #1a1a1a;
    transform: translate(-2px, -2px);
  }

  &:active {
    transform: scale(0.96);
    box-shadow: 2px 2px 0px 0px #1a1a1a;
  }

  &.rough-button-icon:hover {
    box-shadow: none;
    transform: scale(1.1);
  }

  &.rough-button-icon:active {
    transform: scale(1);
  }
`
