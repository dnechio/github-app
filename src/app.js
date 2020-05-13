'use strict'

import React, { Component } from 'react'
import AppContent from './components/app-content'
import ajax from '@fdaciuk/ajax'

class App extends Component {
  constructor () {
    super()
    this.state = {
      repos: [],
      starred: []
    }
  }

  getGitHubApiUrl (username, type) {
    const internalUser = username ? `/${username}` : ''
    const internalType = type ? `/${type}` : ''
    return `https://api.github.com/users${internalUser}${internalType}`
  }

  handleSearch (e) {
    const value = e.target.value
    const keyCode = e.which || e.keyCode
    const ENTER = 13
    const target = e.target

    if (keyCode === ENTER) {
      target.disabled = true

      ajax().get(this.getGitHubApiUrl(value)).then((result) => {
        this.setState({
          userInfo: {
            login: result.login,
            username: result.name,
            photoUrl: result.avatar_url,
            repos: result.public_repos,
            followers: result.followers,
            following: result.following
          },
          repos: [],
          starred: []
        }) 
      })
      .always(() => target.disabled = false)
    }
  }

  getRepos (type) {
    return (e) => {
      const username = this.state.userInfo.login
      const url = this.getGitHubApiUrl(username, type)

      ajax().get(this.getGitHubApiUrl(value)).then((result) => {
        this.setState({
          [type]: result.map((repo) => ({
            name: repo.name,
            link: repo.html_url
          }))
        })
      })
    }
  }

  render () {
    return (
      <AppContent
        userInfo={this.state.userInfo}
        repos={this.state.repos}
        starred={this.state.starred}
        handleSearch={(e) => this.handleSearch(e)}
        getRepos={this.getRepos('repos')}
        getStarred={this.getRepos('starred')}
      />
    )
  }
}

export default App
