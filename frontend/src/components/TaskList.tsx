import * as React from 'react'
import styled from 'styled-components'
import { Header } from './Typography'
import TaskCard from './TaskCard'

const TaskListWrapper = styled.div`
  display: grid;
  background-color: #c4c4c4;
  grid-column: 1 / 5;
  grid-row: 1 / 7;
  grid-template-rows: repeat(12, 1fr);
  grid-template-columns: repeat(4, 1fr);
  padding: 0 1.25em;
`

export default class TaskList extends React.Component {
  render() {
    return (
      <TaskListWrapper>
        <Header>Tasks</Header>
        <TaskCard
          name="Go grocery shopping"
          dueDate="March 14"
          isActive={true}
          isRecurrent={false}
          flags="Personal"
          description=""
        />
      </TaskListWrapper>
    )
  }
}
