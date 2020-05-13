'use strict'

import React, { PropTypes } from 'react'

const UserInfo = ({ userInfo }) => (
  <div className='user-info'>
    <img src={userInfo.photoUrl} />
    <h1 className='username'>
      <a href={`https://github.com/${userInfo.login}`}>
        {userInfo.username}
      </a>
    </h1>
    <ul className='repos-info'>
      <li>Repositorios: {userInfo.repos}</li>
      <li>Seguidores: {userInfo.followers}</li>
      <li>Seguindo: {userInfo.following}</li>
    </ul>
  </div>
)

UserInfo.propTypes = {
  userInfo: PropTypes.shape({
    login: PropTypes.string.isRequired,
    username: PropTypes.string.isRequired,
    photoUrl: PropTypes.string.isRequired,
    repos: PropTypes.number.isRequired,
    followers: PropTypes.number.isRequired,
    following: PropTypes.number.isRequired
  })
}

export default UserInfo
