
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom'
import Main from './components/Main/Main'
import './scss/styles.scss'

function App() {

  return (
    <Router>
      <Routes>
        <Route path="/" element={<Main />} />
      </Routes>
    </Router>
  )
}

export default App
