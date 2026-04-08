import styled from 'styled-components'

type HandDrawnUnderlineProps = {
  color?: string
  className?: string
  children: React.ReactNode
}

const Wrapper = styled.span<{ $color: string }>`
  position: relative;
  display: inline-block;

  &::after {
    content: '';
    position: absolute;
    bottom: -4px;
    left: 0;
    width: 100%;
    height: 4px;
    background: url('data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 20"><path d="M0 10 Q 25 0, 50 10 T 100 10" fill="none" stroke="%23${({ $color }) => $color}" stroke-linecap="round" stroke-width="4"/></svg>') no-repeat;
    background-size: 100% 100%;
  }
`

export default function HandDrawnUnderline({
  color = '0041e0',
  className,
  children,
}: HandDrawnUnderlineProps) {
  return (
    <Wrapper $color={color} className={className}>
      {children}
    </Wrapper>
  )
}
