import React from 'react';
import { BrowserRouter as Router, Route, Routes } from 'react-router-dom';
import Home from './Home';
import Categorize from './Categorize';
import './App.css';
import Trends from "./Trends";

function App() {
    return (
        <Router>
            <div className="App">
                <Routes>
                    <Route path="/" element={<Home />} />
                    <Route path="/categorize" element={<Categorize />} />
                    <Route path="/trends" element={<Trends />} />
                </Routes>
            </div>
        </Router>
    );
}

export default App;
