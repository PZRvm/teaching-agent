import styled from 'styled-components'

/**
 * 示例组件 - 按照项目规范编写
 * 组件说明写在这里
 */
export default function Example() {
  // 组件逻辑...

  return (
    <Wrapper>
      <h1 className="header">标题</h1>
      <div className="content">
        <p className="text">内容</p>
      </div>
    </Wrapper>
  )
}

// 只有一个 Wrapper 样式组件
// 内部使用 class 选择器，支持多层嵌套
const Wrapper = styled.div`
  padding: 20px;

  .header {
    font-size: 24px;
    color: #333;
  }

  .content {
    padding: 10px;

    .text {
      font-size: 16px;
      color: #666;
    }
  }
`
