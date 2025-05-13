import React, {useEffect, useState} from 'react';
import axios from 'axios';
import './Home.css';
import {Link} from 'react-router-dom';

function Home() {
    const [pivotData, setPivotData] = useState([]);
    const [categories, setCategories] = useState([]);
    const [months, setMonths] = useState([]);
    const [totalAmount, setTotalAmount] = useState(null);

    const categoryGroups = {
        Income: ['INCOME'],
        Needs: ['BILLS', 'GROCERIES', 'TRANSPORT'],
        Wants: ['SHOPPING', 'ENTERTAINMENT', 'EATING_OUT', 'PERSONAL_CARE', 'TRAVEL', 'CHARITY', 'GIFTS'],
        Savings: ['EMERGENCY_FUND', 'LISA', 'ISA']
    };

    const processPivotData = (data) => {
        if (!data || data.length === 0) {
            console.warn("No data available for pivot table.");
            return;
        }

        const customOrder = [
            ...categoryGroups.Income,
            '',
            ...categoryGroups.Needs,
            '',
            'Total Needs',
            '',
            ...categoryGroups.Wants,
            '',
            'Total Wants',
            '',
            ...categoryGroups.Savings,
            '',
            'Total Savings'
        ];

        const uniqueMonths = Array.from(new Set(data.map(item => item.month))).sort((a, b) => b.localeCompare(a));
        const pivotData = [];

        const calculateGroupSum = (group) => {
            return uniqueMonths.map(month => {
                const sum = data
                    .filter(item =>
                        group.includes((item.category || "").trim().toUpperCase()) &&
                        item.month.trim() === month
                    )
                    .reduce((acc, item) => acc + (parseFloat(item.amount) || 0), 0);
                return sum.toFixed(2);
            });
        };

        const addRow = (category, isTotal = false) => {
            const row = {category, allTimeTotal: 0, yearTotal: 0};
            const currentYear = new Date().getFullYear().toString();

            uniqueMonths.forEach(month => {
                let monthlyAmount = 0;

                if (isTotal) {
                    monthlyAmount = parseFloat(calculateGroupSum(categoryGroups[category])[uniqueMonths.indexOf(month)]) || 0;
                } else {
                    const record = data.find(item => item.category === category && item.month === month);
                    monthlyAmount = record && record.amount != null ? parseFloat(record.amount) : 0;
                }

                row[month] = monthlyAmount.toFixed(2);
                row.allTimeTotal += monthlyAmount;
                if (month.startsWith(currentYear)) {
                    row.yearTotal += monthlyAmount;
                }
            });

            row.allTimeTotal = row.allTimeTotal.toFixed(2);
            row.yearTotal = row.yearTotal.toFixed(2);

            pivotData.push(row);
        };

        customOrder.forEach(category => {
            if (category === '') {
                pivotData.push({category: ''});
            } else if (category.startsWith('Total')) {
                addRow(category.split(' ')[1], true);
            } else {
                addRow(category);
            }
        });

        setMonths(uniqueMonths);
        setPivotData(pivotData);
    };

    useEffect(() => {
        const fetchTotal = async () => {
            try {
                const response = await axios.get("http://localhost:8000/total");
                setTotalAmount(response.data.total);
            } catch (error) {
                console.error("Error fetching total:", error);
            }
        };
        fetchTotal();
    }, []);

    useEffect(() => {
        const fetchTransactions = async () => {
            try {
                const response = await axios.get(`http://localhost:8000/pivot_data`);
                processPivotData(response.data);
            } catch (error) {
                console.error("Error fetching transactions:", error);
            }
        };
        fetchTransactions();
    }, []);

    const getRowClassName = (category, index) => {
        let group = '';
        if (categoryGroups.Income.includes(category)) {
            group = 'green';
        } else if (categoryGroups.Needs.includes(category) || category === 'Needs') {
            group = 'red';
        } else if (categoryGroups.Wants.includes(category) || category === 'Wants') {
            group = 'blue';
        } else if (categoryGroups.Savings.includes(category) || category === 'Savings') {
            group = 'green';
        }

        if (group === 'red') {
            return index % 2 === 0 ? 'red-odd' : 'red-even';
        } else if (group === 'blue') {
            return index % 2 === 0 ? 'blue-odd' : 'blue-even';
        } else if (group === 'green') {
            return index % 2 === 0 ? 'green-odd' : 'green-even';
        }
        return '';
    };

    const currentYear = new Date().getFullYear();

    return (
        <div className="App">
            <h1>Monthly Expense Summary</h1>

            <div className="total-box">
                <h2>Available to spend: £{parseFloat(totalAmount || 0).toFixed(2)}</h2>
            </div>

            <Link to="/trends">
            <button>View Category Trends</button>
            </Link>

            <table>
                <thead>
                <tr>
                    <th>All-Time</th>
                    <th>{currentYear} Total</th>
                    <th>Category</th>
                    {months.map(month => (
                        <th key={month}>
                            <Link to={`/categorize?month=${month}&uncategorized=false`}>
                                {month}
                            </Link>
                        </th>
                    ))}
                </tr>
                </thead>

                <tbody>
                {pivotData.map((row, rowIndex) => (
                    row.category === '' ? (
                        <tr key={rowIndex}>
                            <td colSpan={months.length + 3} style={{height: '10px'}}></td>
                        </tr>
                    ) : (
                        <tr key={row.category} className={getRowClassName(row.category, rowIndex)}>
                            <td>{row.allTimeTotal || '0.00'}</td>
                            <td>{row.yearTotal || '0.00'}</td>
                            <td>{row.category}</td>
                            {months.map(month => (
                                <td key={month}>{row[month] || '0.00'}</td>
                            ))}
                        </tr>
                    )
                ))}
                </tbody>
            </table>
        </div>
    );
}

export default Home;
