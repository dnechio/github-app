'use strict'

import React from 'react'
import Search from './search'
import UserInfo from './user-info'
import Actions from './actions'
import Repos from './repos'

const AppContent = ({ userInfo, repos, starred }) => (
  <div className='app'>
    <Search />

    {!!userInfo && <UserInfo userInfo={userInfo} />}
    {!!userInfo && <Actions />}

    {!!repos.lenth &&
      <Repos
        className='repos'
        title='Repositórios'
        repos={repos}
      />
    }

    {!!starred.lenth &&
      <Repos
        className='starred'
        title='Favoritos'
        repos={starred}
      />
    }

  </div>
)

AppContent.propTypes = {
  userInfo: React.PropTypes.object,
  repos: React.PropTypes.array.isRequired,
  starred: React.PropTypes.array.isRequired
}

export default AppContent
