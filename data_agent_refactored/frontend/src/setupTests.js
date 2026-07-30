import '@testing-library/jest-dom/vitest'

// jsdom does not implement matchMedia, which antd's responsive observer uses.
Object.defineProperty(window, 'matchMedia', {
  writable: true,
  value: (query) => ({
    matches: false,
    media: query,
    onchange: null,
    addListener: () => {},
    removeListener: () => {},
    addEventListener: () => {},
    removeEventListener: () => {},
    dispatchEvent: () => false,
  }),
})

window.getComputedStyle = () => ({
  boxSizing: 'border-box',
  fontSize: '14px',
  lineHeight: '22px',
  paddingTop: '4px',
  paddingBottom: '4px',
  borderTopWidth: '1px',
  borderBottomWidth: '1px',
  getPropertyValue: (property) => {
    const values = {
      'box-sizing': 'border-box',
      'font-size': '14px',
      'line-height': '22px',
      'padding-top': '4px',
      'padding-bottom': '4px',
      'border-top-width': '1px',
      'border-bottom-width': '1px',
    }
    return values[property] || ''
  },
})

Element.prototype.scrollIntoView = Element.prototype.scrollIntoView || (() => {})
