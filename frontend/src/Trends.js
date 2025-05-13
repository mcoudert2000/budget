import React, { useEffect, useState } from 'react';
import axios from 'axios';
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer
} from 'recharts';
import './Trends.css';

function Trends() {
  const [categories, setCategories] = useState([]);
  const [selectedCategory, setSelectedCategory] = useState('');
  const [chartData, setChartData] = useState([]);
  const [years, setYears] = useState([]);
  const [groupCharts, setGroupCharts] = useState({
    Needs: [],
    Wants: [],
    Savings: []
  });
  const currentYear = new Date().getFullYear();
  const currentMonth = new Date().getMonth(); // Zero-indexed

  const categoryGroups = {
        Income: ['INCOME'],
        Needs: ['BILLS', 'GROCERIES', 'TRANSPORT'],
        Wants: ['SHOPPING', 'ENTERTAINMENT', 'EATING_OUT', 'PERSONAL_CARE', 'TRAVEL', 'CHARITY', 'GIFTS'],
        Savings: ['EMERGENCY_FUND', 'LISA', 'ISA']
    };

  useEffect(() => {
    axios.get('http://localhost:8000/transactions/')
      .then(res => {
        const cats = Array.from(new Set(res.data.map(t => t.category || 'UNKNOWN')));
        setCategories(cats.sort());
      })
      .catch(console.error);
  }, []);

  useEffect(() => {
    if (!selectedCategory) return;

    axios.get(`http://localhost:8000/category_spend?category=${selectedCategory}`)
      .then(res => {
        const data = res.data;

        const yrs = Array.from(new Set(data.map(d => d.year))).sort();
        setYears(yrs);

        const monthNames = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'];
        const accum = {};
        monthNames.forEach(m => {
          accum[m] = { month: m };
          yrs.forEach(y => accum[m][y] = 0);
        });

        data.forEach(({ year, month, amount }) => {
          if (accum[month]) accum[month][year] += parseFloat(amount);
        });

        yrs.forEach(y => {
          let run = 0;
          monthNames.forEach(m => {
            run += accum[m][y];
            accum[m][y] = run;
          });
        });

        monthNames.forEach((m, i) => {
          if (i > currentMonth && accum[m][currentYear]) {
            accum[m][currentYear] = null;
          }
        });

        const final = monthNames.map(m => accum[m]);
        setChartData(final);
      })
      .catch(console.error);
  }, [selectedCategory]);

  useEffect(() => {
    const fetchGroupData = async () => {
      const monthNames = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'];
      const fetchedGroupCharts = {};

      for (let group in categoryGroups) {
        const subcategories = categoryGroups[group];
        const allData = [];

        for (let cat of subcategories) {
          try {
            const response = await axios.get(`http://localhost:8000/category_spend?category=${encodeURIComponent(cat)}`);
            allData.push(...response.data);
          } catch (error) {
            console.error(`Error fetching ${cat}:`, error);
          }
        }

        const yrs = Array.from(new Set(allData.map(d => d.year))).sort();
        const accum = {};
        monthNames.forEach(m => {
          accum[m] = { month: m };
          yrs.forEach(y => accum[m][y] = 0);
        });

        allData.forEach(({ year, month, amount }) => {
          if (accum[month]) {
            accum[month][year] += parseFloat(amount);
          }
        });

        yrs.forEach(y => {
          let run = 0;
          monthNames.forEach(m => {
            run += accum[m][y];
            accum[m][y] = run;
          });
        });

        monthNames.forEach((m, i) => {
          if (i > currentMonth && accum[m][currentYear]) {
            accum[m][currentYear] = null;
          }
        });

        fetchedGroupCharts[group] = monthNames.map(m => accum[m]);
      }

      setGroupCharts(fetchedGroupCharts);
    };

    fetchGroupData();
  }, []);

  const colorMap = {
    2022: '#FF5733',
    2023: '#33FF57',
    2024: '#3357FF',
    2025: '#FF33A1',
  };

  return (
    <div className="chart-container">
      <h2>Category Trends</h2>

      {['Needs', 'Wants', 'Savings'].map(group => (
        <div key={group} style={{ marginBottom: '2rem' }}>
          <h3>{group}</h3>
          <ResponsiveContainer width="100%" height={200}>
            <LineChart data={groupCharts[group] || []}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="month" />
              <YAxis />
              <Tooltip />
              <Legend />
              {years.map(y => (
                <Line
                  key={y}
                  type="monotone"
                  dataKey={String(y)}
                  stroke={colorMap[y] || '#888'}
                  strokeWidth={y === currentYear ? 3 : 2}
                  dot={false}
                  name={String(y)}
                />
              ))}
            </LineChart>
          </ResponsiveContainer>
        </div>
      ))}

      <select
        value={selectedCategory}
        onChange={e => setSelectedCategory(e.target.value)}
      >
        <option value="">-- Select a category --</option>
        {categories.map(cat => (
          <option key={cat} value={cat}>{cat}</option>
        ))}
      </select>

      {selectedCategory && (
        <div style={{ marginTop: '2rem' }}>
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="month" />
              <YAxis />
              <Tooltip />
              <Legend />
              {years.map(y => (
                <Line
                  key={y}
                  type="monotone"
                  dataKey={String(y)}
                  stroke={colorMap[y] || '#888'}
                  strokeWidth={y === currentYear ? 3 : 2}
                  dot={false}
                  name={String(y)}
                />
              ))}
            </LineChart>
          </ResponsiveContainer>
        </div>
      )}
    </div>
  );
}

export default Trends;
