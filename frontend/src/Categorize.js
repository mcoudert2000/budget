import React, { useEffect, useState } from 'react';
import axios from 'axios';
import './Categorize.css';
import {Link, useLocation} from 'react-router-dom';


const categories = [
    "GROCERIES", "SHOPPING", "PERSONAL_CARE", "TRANSPORT", "TRANSFERS",
    "BILLS", "NEEDS", "TRAVEL", "EATING_OUT", "INCOME", "ENTERTAINMENT",
    "EMERGENCY_FUND", "CHARITY", "GIFTS", "LISA", "ISA", "TAX", "UNKNOWN"
];

function Categorize() {
    const [transactions, setTransactions] = useState([]);
    const [selectedCategory, setSelectedCategory] = useState("");
    const [selectedTransactions, setSelectedTransactions] = useState([]);
    const [sortConfig, setSortConfig] = useState({ key: 'transaction_id', direction: 'asc' });
    const [refreshData, setRefreshData] = useState(false);

    const uncategorizedCount = transactions.filter(txn => !txn.category || txn.category.trim() === '').length;

    const location = useLocation();
    const queryParams = new URLSearchParams(location.search);
    const selectedMonth = queryParams.get('month') || '';
    const uncategorizedParam = queryParams.get('uncategorized');
    const getUncategorized = uncategorizedParam === null ? true : uncategorizedParam.toLowerCase() === 'true';

    const selectedTotal = selectedTransactions
    .map(id => transactions.find(txn => txn.transaction_id === id))
    .filter(txn => txn) // Ensure transaction exists
    .reduce((sum, txn) => sum + txn.amount, 0);

    // Fetch uncategorized transactions on mount
    useEffect(() => {
        fetch(`http://localhost:8000/transactions?uncategorized=${getUncategorized}&month=${selectedMonth}`)
            .then(response => response.json())
            .then(data => {
                setTransactions(data);
            })
            .catch(error => console.error("Error fetching transactions:", error));
    }, [getUncategorized, refreshData, selectedMonth]);

    // Handle category change
    const handleCategoryChange = (e) => {
        setSelectedCategory(e.target.value);
    };

    const handleTransactionSelect = (id, e) => {
        const isCtrlKey = e.ctrlKey || e.metaKey;
        const isShiftKey = e.shiftKey;

        if (isShiftKey && selectedTransactions.length > 0) {
            const lastSelected = selectedTransactions[selectedTransactions.length - 1];
            const lastIndex = transactions.findIndex(txn => txn.transaction_id === lastSelected);
            const currentIndex = transactions.findIndex(txn => txn.transaction_id === id);
            const range = transactions.slice(Math.min(lastIndex, currentIndex), Math.max(lastIndex, currentIndex) + 1);
            const newSelection = range.map(txn => txn.transaction_id);
            setSelectedTransactions(prev => [...new Set([...prev, ...newSelection])]);  // Avoid duplicates
        } else if (isCtrlKey || e.metaKey) {
            setSelectedTransactions(prevSelected => {
                if (prevSelected.includes(id)) {
                    return prevSelected.filter(txnId => txnId !== id);
                } else {
                    return [...prevSelected, id];
                }
            });
        } else {
            setSelectedTransactions([id]);
        }
    };

    // Submit category update for selected transactions
    const handleCategorize = () => {
        if (!selectedCategory) {
            return alert("Please select a category");
        }
        if (selectedTransactions.length === 0) {
            return alert("Please select at least one transaction");
        }

        axios.put("http://localhost:8000/categorize_multiple/", {
            transaction_ids: selectedTransactions,
            user_category: selectedCategory
        })
            .then(() => {
                alert("Transactions categorized successfully");
                setSelectedTransactions([]);
                setRefreshData(prev => !prev);

            })
            .catch(error => console.error("Error updating categories:", error));
    };

     const handleSort = (key) => {
        let direction = 'asc';
        if (sortConfig.key === key && sortConfig.direction === 'asc') {
            direction = 'desc';
        }

        const sortedTransactions = [...transactions].sort((a, b) => {
            if (a[key] < b[key]) {
                return direction === 'asc' ? -1 : 1;
            }
            if (a[key] > b[key]) {
                return direction === 'asc' ? 1 : -1;
            }
            return 0;
        });

        setTransactions(sortedTransactions);
        setSortConfig({ key, direction });
    };

    return (
        <div className="App">
            <h1>Transaction Categorizer</h1>
            <Link to="/">← Back to Home</Link>
            <div>
                <p>{uncategorizedCount} transactions still uncategorized</p>
                <p>Selected total: £{selectedTotal.toFixed(2)}</p>
                <select
                    value={selectedCategory}
                    onChange={handleCategoryChange}
                >
                    <option value="">Select Category</option>
                    {categories.map(cat => (
                        <option key={cat} value={cat}>{cat}</option>
                    ))}
                </select>
                <button onClick={handleCategorize}>Categorize Selected</button>
            </div>
            <table>
                <thead>
                <tr>
                    <th onClick={() => handleSort('transaction_id')}>
                        ID {sortConfig.key === 'transaction_id' && (sortConfig.direction === 'asc' ? '↑' : '↓')}
                    </th>
                    <th onClick={() => handleSort('date')}>
                        Date {sortConfig.key === 'date' && (sortConfig.direction === 'asc' ? '↑' : '↓')}
                    </th>
                    <th onClick={() => handleSort('description')}>
                        Description {sortConfig.key === 'description' && (sortConfig.direction === 'asc' ? '↑' : '↓')}
                    </th>
                    <th onClick={() => handleSort('amount')}>
                        Amount {sortConfig.key === 'amount' && (sortConfig.direction === 'asc' ? '↑' : '↓')}
                    </th>
                    <th onClick={() => handleSort('account')}>
                        Account {sortConfig.key === 'account' && (sortConfig.direction === 'asc' ? '↑' : '↓')}
                    </th>
                    <th onClick={() => handleSort('category')}>
                        Category {sortConfig.key === 'category' && (sortConfig.direction === 'asc' ? '↑' : '↓')}
                    </th>
                </tr>
                </thead>
                <tbody>
                {transactions.map(txn => (
                    <tr
                        key={txn.transaction_id}
                        onClick={(e) => handleTransactionSelect(txn.transaction_id, e)}  // Add onClick to the row
                        style={{backgroundColor: selectedTransactions.includes(txn.transaction_id) ? 'lightblue' : ''}}
                    >
                        <td>{txn.transaction_id}</td>
                        <td>{txn.date}</td>
                        <td>{txn.description}</td>
                        <td>{txn.amount}</td>
                        <td>{txn.account}</td>
                        <td>{txn.category}</td>
                    </tr>
                ))}
                </tbody>
            </table>
        </div>
    );
}

export default Categorize;
