import styled from 'styled-components'

type RoughInputProps = React.InputHTMLAttributes<HTMLInputElement> & {
  className?: string
}

const Wrapper = styled.input`
  background: white;
  border: 3px solid #1A1A1A;
  padding: 12px 16px;
  font-size: 16px;
  box-shadow: 2px 2px 0px 0px #1A1A1A;
  outline: none;
  transition: box-shadow 0.2s ease;
  width: 100%;

  &::placeholder {
    color: #d4d4d4;
  }

  &:focus {
    box-shadow: 4px 4px 0px 0px #0041e0;
  }
`

export default function RoughInput({ className, ...rest }: RoughInputProps) {
  return <Wrapper className={className} {...rest} />
}
