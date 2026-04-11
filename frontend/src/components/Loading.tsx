// frontend/src/components/Loading.tsx
import styled from 'styled-components'
import { keyframes } from 'styled-components'

const rotate = keyframes`
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
`

interface LoadingProps {
  size?: 'small' | 'medium' | 'large'
  message?: string
}

export default function Loading({ size = 'medium', message }: LoadingProps) {
  const sizeMap = {
    small: 24,
    medium: 40,
    large: 60,
  }

  const borderWidth = {
    small: 3,
    medium: 4,
    large: 5,
  }

  return (
    <Wrapper>
      <Spinner
        $size={sizeMap[size]}
        $borderWidth={borderWidth[size]}
      >
        <SpinnerInner />
      </Spinner>
      {message && <Message>{message}</Message>}
    </Wrapper>
  )
}

const Wrapper = styled.div`
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 16px;
`

const Spinner = styled.div<{ $size: number; $borderWidth: number }>`
  width: ${(props) => props.$size}px;
  height: ${(props) => props.$size}px;
  border: ${(props) => props.$borderWidth}px solid #1A1A1A;
  border-top-color: transparent;
  border-radius: 50%;
  animation: ${rotate} 1s linear infinite;
`

const SpinnerInner = styled.div`
  width: 100%;
  height: 100%;
  border: 2px dashed rgba(26, 26, 26, 0.3);
  border-radius: 50%;
  animation: ${rotate} 0.8s linear infinite reverse;
`

const Message = styled.p`
  margin: 0;
  font-size: 14px;
  font-weight: 600;
  color: #1A1A1A;
  text-align: center;
`
