'use strict'

import React, { Component } from 'react'
import AppContent from './components/app-content'

class App extends Component {
  constructor () {
    super()
    this.state = {
      userInfo: {
        login: 'fdaciuk',
        username: 'Daniel Necchio',
        photoUrl: 'https://avatars2.githubusercontent.com/u/487669?v=3',
        repos: 12,
        followers: 15,
        following: 20
      },
      repos: [{
        name: 'Repositorio mock',
        link: '#'
      }],
      starred: [{
        name: 'Favorito mock',
        link: '#'
      }]
    }
  }

  render () {
    return (
      <AppContent
        userInfo={this.state.userInfo}
        repos={this.state.repos}
        starred={this.state.starred}
      />
    )
  }
}

export default App
