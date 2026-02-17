import unittest
from datetime import datetime
from unittest.mock import patch, MagicMock
import sys
import os

# Add the current directory to the path to import accounts module
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import the module to test
from accounts import Account, get_share_price

class TestGetSharePrice(unittest.TestCase):
    """Test cases for the get_share_price function"""
    
    def test_get_share_price_valid_symbols(self):
        """Test get_share_price with valid symbols"""
        self.assertEqual(get_share_price("AAPL"), 150.0)
        self.assertEqual(get_share_price("TSLA"), 800.0)
        self.assertEqual(get_share_price("GOOGL"), 2800.0)
    
    def test_get_share_price_invalid_symbol(self):
        """Test get_share_price with invalid symbol raises ValueError"""
        with self.assertRaises(ValueError):
            get_share_price("INVALID")
    
    def test_get_share_price_case_sensitive(self):
        """Test get_share_price is case sensitive"""
        with self.assertRaises(ValueError):
            get_share_price("aapl")
        with self.assertRaises(ValueError):
            get_share_price("Googl")

class TestAccountInitialization(unittest.TestCase):
    """Test cases for Account class initialization"""
    
    def test_account_initialization(self):
        """Test Account initialization with valid account_id"""
        account = Account("test_account_123")
        
        self.assertEqual(account.account_id, "test_account_123")
        self.assertEqual(account.balance, 0.0)
        self.assertEqual(account.initial_deposit, 0.0)
        self.assertEqual(account.holdings, {})
        self.assertEqual(account.transactions, [])
    
    def test_account_initialization_empty_id(self):
        """Test Account initialization with empty account_id"""
        account = Account("")
        self.assertEqual(account.account_id, "")
    
    def test_account_initialization_numeric_id(self):
        """Test Account initialization with numeric account_id"""
        account = Account("12345")
        self.assertEqual(account.account_id, "12345")

class TestAccountDeposit(unittest.TestCase):
    """Test cases for Account deposit method"""
    
    def setUp(self):
        """Set up a fresh account for each test"""
        self.account = Account("test_account")
    
    def test_deposit_positive_amount(self):
        """Test deposit with positive amount"""
        self.account.deposit(100.0)
        self.assertEqual(self.account.balance, 100.0)
        self.assertEqual(self.account.initial_deposit, 100.0)
        self.assertEqual(len(self.account.transactions), 1)
    
    def test_deposit_multiple_times(self):
        """Test multiple deposits"""
        self.account.deposit(50.0)
        self.account.deposit(75.0)
        self.assertEqual(self.account.balance, 125.0)
        self.assertEqual(self.account.initial_deposit, 50.0)
        self.assertEqual(len(self.account.transactions), 2)
    
    def test_deposit_zero_amount(self):
        """Test deposit with zero amount raises ValueError"""
        with self.assertRaises(ValueError):
            self.account.deposit(0.0)
    
    def test_deposit_negative_amount(self):
        """Test deposit with negative amount raises ValueError"""
        with self.assertRaises(ValueError):
            self.account.deposit(-10.0)
    
    def test_deposit_fractional_amount(self):
        """Test deposit with fractional amount"""
        self.account.deposit(99.99)
        self.assertEqual(self.account.balance, 99.99)
    
    def test_deposit_initial_deposit_only_first(self):
        """Test that initial_deposit is only set on first deposit"""
        self.account.deposit(100.0)
        self.account.deposit(200.0)
        self.assertEqual(self.account.initial_deposit, 100.0)

class TestAccountWithdraw(unittest.TestCase):
    """Test cases for Account withdraw method"""
    
    def setUp(self):
        """Set up a fresh account with balance for each test"""
        self.account = Account("test_account")
        self.account.deposit(200.0)
    
    def test_withdraw_sufficient_balance(self):
        """Test withdraw with sufficient balance"""
        result = self.account.withdraw(100.0)
        self.assertTrue(result)
        self.assertEqual(self.account.balance, 100.0)
        self.assertEqual(len(self.account.transactions), 2)
    
    def test_withdraw_insufficient_balance(self):
        """Test withdraw with insufficient balance"""
        result = self.account.withdraw(300.0)
        self.assertFalse(result)
        self.assertEqual(self.account.balance, 200.0)
        self.assertEqual(len(self.account.transactions), 1)  # Only deposit transaction
    
    def test_withdraw_exact_balance(self):
        """Test withdraw exact balance amount"""
        result = self.account.withdraw(200.0)
        self.assertTrue(result)
        self.assertEqual(self.account.balance, 0.0)
    
    def test_withdraw_zero_amount(self):
        """Test withdraw with zero amount raises ValueError"""
        with self.assertRaises(ValueError):
            self.account.withdraw(0.0)
    
    def test_withdraw_negative_amount(self):
        """Test withdraw with negative amount raises ValueError"""
        with self.assertRaises(ValueError):
            self.account.withdraw(-10.0)
    
    def test_withdraw_fractional_amount(self):
        """Test withdraw with fractional amount"""
        result = self.account.withdraw(99.99)
        self.assertTrue(result)
        self.assertAlmostEqual(self.account.balance, 100.01, places=2)
    
    def test_withdraw_multiple_times(self):
        """Test multiple withdrawals"""
        self.account.withdraw(50.0)
        self.account.withdraw(30.0)
        self.assertEqual(self.account.balance, 120.0)
        self.assertEqual(len(self.account.transactions), 3)

class TestAccountBuyShares(unittest.TestCase):
    """Test cases for Account buy_shares method"""
    
    def setUp(self):
        """Set up a fresh account with balance for each test"""
        self.account = Account("test_account")
        self.account.deposit(10000.0)
    
    def test_buy_shares_sufficient_balance(self):
        """Test buying shares with sufficient balance"""
        result = self.account.buy_shares("AAPL", 10)
        self.assertTrue(result)
        self.assertEqual(self.account.balance, 10000.0 - (150.0 * 10))
        self.assertEqual(self.account.holdings, {"AAPL": 10})
        self.assertEqual(len(self.account.transactions), 2)
    
    def test_buy_shares_insufficient_balance(self):
        """Test buying shares with insufficient balance"""
        result = self.account.buy_shares("GOOGL", 10)  # 10 * 2800 = 28000 > 10000
        self.assertFalse(result)
        self.assertEqual(self.account.balance, 10000.0)
        self.assertEqual(self.account.holdings, {})
        self.assertEqual(len(self.account.transactions), 1)  # Only deposit transaction
    
    def test_buy_shares_invalid_symbol(self):
        """Test buying shares with invalid symbol"""
        result = self.account.buy_shares("INVALID", 10)
        self.assertFalse(result)
        self.assertEqual(self.account.balance, 10000.0)
        self.assertEqual(self.account.holdings, {})
    
    def test_buy_shares_zero_quantity(self):
        """Test buying shares with zero quantity raises ValueError"""
        with self.assertRaises(ValueError):
            self.account.buy_shares("AAPL", 0)
    
    def test_buy_shares_negative_quantity(self):
        """Test buying shares with negative quantity raises ValueError"""
        with self.assertRaises(ValueError):
            self.account.buy_shares("AAPL", -5)
    
    def test_buy_shares_multiple_purchases_same_symbol(self):
        """Test multiple purchases of the same symbol"""
        self.account.buy_shares("AAPL", 5)
        self.account.buy_shares("AAPL", 3)
        self.assertEqual(self.account.holdings, {"AAPL": 8})
        self.assertEqual(self.account.balance, 10000.0 - (150.0 * 8))
    
    def test_buy_shares_multiple_symbols(self):
        """Test buying shares of multiple different symbols"""
        self.account.buy_shares("AAPL", 10)
        self.account.buy_shares("TSLA", 5)
        self.assertEqual(self.account.holdings, {"AAPL": 10, "TSLA": 5})
        expected_balance = 10000.0 - (150.0 * 10) - (800.0 * 5)
        self.assertEqual(self.account.balance, expected_balance)
    
    def test_buy_shares_exact_balance(self):
        """Test buying shares using exact balance"""
        # Calculate how many AAPL shares we can buy with 10000 balance
        shares_to_buy = int(10000.0 / 150.0)  # 66 shares * 150 = 9900
        result = self.account.buy_shares("AAPL", shares_to_buy)
        self.assertTrue(result)
        self.assertEqual(self.account.balance, 10000.0 - (150.0 * shares_to_buy))

class TestAccountSellShares(unittest.TestCase):
    """Test cases for Account sell_shares method"""
    
    def setUp(self):
        """Set up a fresh account with holdings for each test"""
        self.account = Account("test_account")
        self.account.deposit(10000.0)
        self.account.buy_shares("AAPL", 20)
        self.account.buy_shares("TSLA", 5)
    
    def test_sell_shares_sufficient_quantity(self):
        """Test selling shares with sufficient quantity"""
        initial_balance = self.account.balance
        result = self.account.sell_shares("AAPL", 10)
        self.assertTrue(result)
        self.assertEqual(self.account.holdings, {"AAPL": 10, "TSLA": 5})
        self.assertEqual(self.account.balance, initial_balance + (150.0 * 10))
        self.assertEqual(len(self.account.transactions), 4)
    
    def test_sell_shares_insufficient_quantity(self):
        """Test selling shares with insufficient quantity"""
        result = self.account.sell_shares("AAPL", 30)
        self.assertFalse(result)
        self.assertEqual(self.account.holdings, {"AAPL": 20, "TSLA": 5})
    
    def test_sell_shares_nonexistent_symbol(self):
        """Test selling shares of a symbol not in holdings"""
        result = self.account.sell_shares("GOOGL", 5)
        self.assertFalse(result)
        self.assertEqual(self.account.holdings, {"AAPL": 20, "TSLA": 5})
    
    def test_sell_shares_zero_quantity(self):
        """Test selling shares with zero quantity raises ValueError"""
        with self.assertRaises(ValueError):
            self.account.sell_shares("AAPL", 0)
    
    def test_sell_shares_negative_quantity(self):
        """Test selling shares with negative quantity raises ValueError"""
        with self.assertRaises(ValueError):
            self.account.sell_shares("AAPL", -5)
    
    def test_sell_shares_all_quantity(self):
        """Test selling all shares of a symbol"""
        result = self.account.sell_shares("AAPL", 20)
        self.assertTrue(result)
        self.assertEqual(self.account.holdings, {"TSLA": 5})
        self.assertNotIn("AAPL", self.account.holdings)
    
    def test_sell_shares_invalid_symbol_price(self):
        """Test selling shares when symbol price becomes invalid"""
        # Mock get_share_price to raise ValueError for TSLA
        with patch('accounts.get_share_price') as mock_get_price:
            mock_get_price.side_effect = lambda s: 150.0 if s == "AAPL" else ValueError("Price not available")
            result = self.account.sell_shares("TSLA", 5)
            self.assertFalse(result)
            self.assertEqual(self.account.holdings, {"AAPL": 20, "TSLA": 5})
    
    def test_sell_shares_multiple_sales(self):
        """Test multiple sales of the same symbol"""
        self.account.sell_shares("AAPL", 5)
        self.account.sell_shares("AAPL", 5)
        self.assertEqual(self.account.holdings, {"AAPL": 10, "TSLA": 5})

class TestAccountPortfolioValue(unittest.TestCase):
    """Test cases for Account get_portfolio_value method"""
    
    def setUp(self):
        """Set up a fresh account with holdings for each test"""
        self.account = Account("test_account")
        self.account.deposit(10000.0)
    
    def test_get_portfolio_value_empty(self):
        """Test portfolio value with no holdings"""
        self.assertEqual(self.account.get_portfolio_value(), 0.0)
    
    def test_get_portfolio_value_single_holding(self):
        """Test portfolio value with single holding"""
        self.account.buy_shares("AAPL", 10)
        expected_value = 150.0 * 10
        self.assertEqual(self.account.get_portfolio_value(), expected_value)
    
    def test_get_portfolio_value_multiple_holdings(self):
        """Test portfolio value with multiple holdings"""
        self.account.buy_shares("AAPL", 10)
        self.account.buy_shares("TSLA", 5)
        self.account.buy_shares("GOOGL", 2)
        
        expected_value = (150.0 * 10) + (800.0 * 5) + (2800.0 * 2)
        self.assertEqual(self.account.get_portfolio_value(), expected_value)
    
    def test_get_portfolio_value_after_sales(self):
        """Test portfolio value after selling some shares"""
        self.account.buy_shares("AAPL", 20)
        self.account.sell_shares("AAPL", 10)
        expected_value = 150.0 * 10
        self.assertEqual(self.account.get_portfolio_value(), expected_value)
    
    def test_get_portfolio_value_with_invalid_symbol(self):
        """Test portfolio value when holdings contain invalid symbol"""
        # Manually add an invalid symbol to holdings
        self.account.holdings = {"AAPL": 10, "INVALID": 5}
        
        # Portfolio value should only include valid symbols
        expected_value = 150.0 * 10
        self.assertEqual(self.account.get_portfolio_value(), expected_value)

class TestAccountProfitOrLoss(unittest.TestCase):
    """Test cases for Account get_profit_or_loss method"""
    
    def setUp(self):
        """Set up a fresh account for each test"""
        self.account = Account("test_account")
    
    def test_get_profit_or_loss_no_deposit(self):
        """Test profit/loss with no initial deposit"""
        self.assertEqual(self.account.get_profit_or_loss(), 0.0)
    
    def test_get_profit_or_loss_positive_profit(self):
        """Test profit/loss with positive profit"""
        self.account.deposit(1000.0)
        self.account.buy_shares("AAPL", 5)  # Cost: 750, Balance: 250
        # Mock portfolio value to be higher
        with patch.object(self.account, 'get_portfolio_value', return_value=1000.0):
            profit_loss = self.account.get_profit_or_loss()
            # Total value = balance (250) + portfolio (1000) = 1250
            # Initial deposit = 1000
            # Profit = 1250 - 1000 = 250
            self.assertEqual(profit_loss, 250.0)
    
    def test_get_profit_or_loss_negative_loss(self):
        """Test profit/loss with negative loss"""
        self.account.deposit(1000.0)
        self.account.buy_shares("AAPL", 10)  # Cost: 1500, but only have 1000, so won't buy
        # Actually buy fewer shares
        self.account.buy_shares("AAPL", 5)  # Cost: 750, Balance: 250
        # Mock portfolio value to be lower
        with patch.object(self.account, 'get_portfolio_value', return_value=500.0):
            profit_loss = self.account.get_profit_or_loss()
            # Total value = balance (250) + portfolio (500) = 750
            # Initial deposit = 1000
            # Loss = 750 - 1000 = -250
            self.assertEqual(profit_loss, -250.0)
    
    def test_get_profit_or_loss_break_even(self):
        """Test profit/loss at break even"""
        self.account.deposit(1000.0)
        # Mock portfolio value to make total equal to initial deposit
        with patch.object(self.account, 'get_portfolio_value', return_value=750.0):
            profit_loss = self.account.get_profit_or_loss()
            # Total value = balance (1000) + portfolio (750) = 1750
            # Wait, balance is 1000, not 0
            # Let's adjust: deposit 1000, don't spend anything
            self.account.balance = 1000.0
            with patch.object(self.account, 'get_portfolio_value', return_value=0.0):
                profit_loss = self.account.get_profit_or_loss()
                self.assertEqual(profit_loss, 0.0)
    
    def test_get_profit_or_loss_with_multiple_deposits(self):
        """Test profit/loss with multiple deposits (only first counts as initial)"""
        self.account.deposit(500.0)
        self.account.deposit(500.0)
        self.account.buy_shares("AAPL", 5)  # Cost: 750, Balance: 250
        
        # Total value = balance (250) + portfolio (750) = 1000
        # Initial deposit = 500
        # Profit = 1000 - 500 = 500
        profit_loss = self.account.get_profit_or_loss()
        self.assertEqual(profit_loss, 500.0)

class TestAccountHoldings(unittest.TestCase):
    """Test cases for Account get_holdings method"""
    
    def setUp(self):
        """Set up a fresh account for each test"""
        self.account = Account("test_account")
    
    def test_get_holdings_empty(self):
        """Test get_holdings with no holdings"""
        holdings = self.account.get_holdings()
        self.assertEqual(holdings, {})
        # Verify it's a copy, not the original