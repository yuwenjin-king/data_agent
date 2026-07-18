import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'

import Login from '../pages/Login'

describe('Login', () => {
  it('renders the login form with username/password fields and a submit button', () => {
    render(
      <MemoryRouter>
        <Login />
      </MemoryRouter>,
    )
    expect(screen.getByText('Data Agent 登录')).toBeInTheDocument()
    expect(screen.getByPlaceholderText('用户名')).toBeInTheDocument()
    expect(screen.getByPlaceholderText('密码')).toBeInTheDocument()
    const submit = screen.getByRole('button')
    expect(submit).toBeInTheDocument()
    expect(submit).toHaveTextContent(/登.*录/)
  })
})
