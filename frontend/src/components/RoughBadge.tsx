import styled from 'styled-components'

type RoughBadgeProps = {
  variant?: 'pink' | 'yellow' | 'blue' | 'green'
  rotation?: number
  className?: string
  children: React.ReactNode
}

const variantColors: Record<string, string> = {
  pink: '#FCE4EC',
  yellow: '#FFF9C4',
  blue: '#E3F2FD',
  green: '#E8F5E9',
}

const Wrapper = styled.span<{ $variant: string; $rotation: number }>`
  display: inline-block;
  padding: 4px 12px;
  background: ${({ $variant }) => variantColors[$variant]};
  border: 2px solid #1A1A1A;
  font-size: 12px;
  font-weight: 700;
  transform: rotate(${({ $rotation }) => $rotation}deg);
  box-shadow: 2px 2px 0px 0px #1A1A1A;
`

export default function RoughBadge({
  variant = 'pink',
  rotation = 2,
  className,
  children,
}: RoughBadgeProps) {
  return (
    <Wrapper $variant={variant} $rotation={rotation} className={className}>
      {children}
    </Wrapper>
  )
}
