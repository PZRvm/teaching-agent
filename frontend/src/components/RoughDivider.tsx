import styled from 'styled-components'

type RoughDividerProps = {
  maxWidth?: string
  className?: string
}

const Wrapper = styled.div<{ $maxWidth: string }>`
  max-width: ${({ $maxWidth }) => $maxWidth};
  margin: 40px auto;
  border: none;
  border-top: 3px solid #1A1A1A;
  transform: skew(-2deg);
  opacity: 0.6;
`

export default function RoughDivider({ maxWidth = '100%', className }: RoughDividerProps) {
  return <Wrapper $maxWidth={maxWidth} className={className} />
}
