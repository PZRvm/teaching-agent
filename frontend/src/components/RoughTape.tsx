import styled from 'styled-components'

type RoughTapeProps = {
  position: 'top-left' | 'top-right'
  className?: string
}

const Wrapper = styled.div<{ $position: 'top-left' | 'top-right' }>`
  width: 64px;
  height: 32px;
  background: rgba(227, 242, 253, 0.6);
  backdrop-filter: blur(1px);
  border-left: 1px solid rgba(0, 0, 0, 0.1);
  border-right: 1px solid rgba(0, 0, 0, 0.1);
  position: absolute;
  top: -16px;
  left: ${({ $position }) => ($position === 'top-left' ? '-8px' : undefined)};
  right: ${({ $position }) => ($position === 'top-right' ? '-8px' : undefined)};
  transform: rotate(${({ $position }) => ($position === 'top-left' ? '-15deg' : '15deg')});
`

export default function RoughTape({ position, className }: RoughTapeProps) {
  return <Wrapper $position={position} className={className} />
}
