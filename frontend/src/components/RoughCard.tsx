import styled from 'styled-components'

type RoughCardProps = {
  variant?: 'blue' | 'green' | 'pink' | 'yellow' | 'white'
  rotation?: number
  tape?: 'top-left' | 'top-right' | 'none'
  className?: string
  children: React.ReactNode
}

const variantColors: Record<string, string> = {
  blue: 'rgba(227, 242, 253, 1)',
  green: 'rgba(232, 245, 233, 1)',
  pink: 'rgba(252, 228, 236, 1)',
  yellow: 'rgba(255, 249, 196, 1)',
  white: 'rgba(250, 250, 250, 1)',
}

export default function RoughCard({
  variant = 'blue',
  rotation = -0.5,
  tape = 'none',
  className,
  children,
}: RoughCardProps) {
  return (
    <Wrapper
      $variant={variant}
      $rotation={rotation}
      className={className}
    >
      {tape !== 'none' && <div className={`tape ${tape}`} />}
      {children}
    </Wrapper>
  )
}

const Wrapper = styled.div<{ $variant: string; $rotation: number }>`
  position: relative;
  background: ${({ $variant }) => variantColors[$variant]};
  border: 3px solid #1A1A1A;
  padding: 40px;
  box-shadow: 4px 4px 0px 0px #1A1A1A;
  transform: rotate(${({ $rotation }) => $rotation}deg);
  transition: all 0.3s ease;

  .tape {
    width: 64px;
    height: 32px;
    background: rgba(227, 242, 253, 0.6);
    backdrop-filter: blur(1px);
    border-left: 1px solid rgba(0, 0, 0, 0.1);
    border-right: 1px solid rgba(0, 0, 0, 0.1);
    position: absolute;
    top: -16px;
  }

  .top-left {
    left: -8px;
    transform: rotate(-15deg);
  }

  .top-right {
    right: -8px;
    transform: rotate(15deg);
  }
`
