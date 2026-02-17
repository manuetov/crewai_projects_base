

from datetime import datetime

def get_share_price(symbol):
    """
    Función que retorna el precio actual de una acción.
    Esta es una implementación de prueba que retorna precios fijos.
    
    Args:
        symbol (str): El símbolo de la acción.
        
    Returns:
        float: El precio actual de la acción.
    """
    prices = {
        "AAPL": 150.0,
        "TSLA": 800.0,
        "GOOGL": 2800.0
    }
    
    if symbol in prices:
        return prices[symbol]
    else:
        raise ValueError(f"Precio no disponible para el símbolo {symbol}")

class Account:
    """
    Clase que representa una cuenta de usuario para una plataforma de simulación de trading.
    """
    
    def __init__(self, account_id):
        """
        Inicializa una nueva cuenta con un ID único.
        
        Args:
            account_id (str): El identificador único de la cuenta.
        """
        self.account_id = account_id
        self.balance = 0.0
        self.initial_deposit = 0.0
        self.holdings = {}
        self.transactions = []
        
    def deposit(self, amount):
        """
        Aumenta el balance de la cuenta en la cantidad especificada.
        
        Args:
            amount (float): La cantidad a depositar.
        """
        if amount <= 0:
            raise ValueError("El monto del depósito debe ser mayor que cero")
            
        self.balance += amount
        
        # Si es el primer depósito, actualizar el depósito inicial
        if self.initial_deposit == 0:
            self.initial_deposit = amount
        
        self._record_transaction("DEPOSIT", f"Depósito de ${amount:.2f}")
        
    def withdraw(self, amount):
        """
        Disminuye el balance de la cuenta en la cantidad especificada si hay fondos suficientes.
        
        Args:
            amount (float): La cantidad a retirar.
            
        Returns:
            bool: True si el retiro fue exitoso, False en caso contrario.
        """
        if amount <= 0:
            raise ValueError("El monto del retiro debe ser mayor que cero")
            
        if self.balance >= amount:
            self.balance -= amount
            self._record_transaction("WITHDRAW", f"Retiro de ${amount:.2f}")
            return True
        else:
            return False
            
    def buy_shares(self, symbol, quantity):
        """
        Registra la compra de una cantidad especificada de acciones de un símbolo dado.
        
        Args:
            symbol (str): El símbolo de la acción a comprar.
            quantity (int): La cantidad de acciones a comprar.
            
        Returns:
            bool: True si la compra fue exitosa, False en caso contrario.
        """
        if quantity <= 0:
            raise ValueError("La cantidad de acciones debe ser mayor que cero")
            
        try:
            price_per_share = get_share_price(symbol)
            total_cost = price_per_share * quantity
            
            if self.balance >= total_cost:
                self.balance -= total_cost
                
                # Actualizar las acciones en holdings
                if symbol in self.holdings:
                    self.holdings[symbol] += quantity
                else:
                    self.holdings[symbol] = quantity
                
                self._record_transaction("BUY", f"Compra de {quantity} acciones de {symbol} a ${price_per_share:.2f} por acción")
                return True
            else:
                return False
        except ValueError:
            return False
            
    def sell_shares(self, symbol, quantity):
        """
        Registra la venta de una cantidad especificada de acciones de un símbolo dado.
        
        Args:
            symbol (str): El símbolo de la acción a vender.
            quantity (int): La cantidad de acciones a vender.
            
        Returns:
            bool: True si la venta fue exitosa, False en caso contrario.
        """
        if quantity <= 0:
            raise ValueError("La cantidad de acciones debe ser mayor que cero")
            
        if symbol in self.holdings and self.holdings[symbol] >= quantity:
            try:
                price_per_share = get_share_price(symbol)
                total_value = price_per_share * quantity
                
                self.balance += total_value
                self.holdings[symbol] -= quantity
                
                # Si ya no hay acciones, eliminar el símbolo de holdings
                if self.holdings[symbol] == 0:
                    del self.holdings[symbol]
                    
                self._record_transaction("SELL", f"Venta de {quantity} acciones de {symbol} a ${price_per_share:.2f} por acción")
                return True
            except ValueError:
                return False
        else:
            return False
            
    def get_portfolio_value(self):
        """
        Calcula y retorna el valor total de las holdings de acciones.
        
        Returns:
            float: El valor total del portafolio de acciones.
        """
        portfolio_value = 0.0
        
        for symbol, quantity in self.holdings.items():
            try:
                price = get_share_price(symbol)
                portfolio_value += price * quantity
            except ValueError:
                # Si no se puede obtener el precio, ignorar esta acción
                pass
                
        return portfolio_value
        
    def get_profit_or_loss(self):
        """
        Calcula y retorna la ganancia o pérdida neta en comparación con el depósito inicial.
        
        Returns:
            float: La ganancia o pérdida neta.
        """
        total_value = self.balance + self.get_portfolio_value()
        return total_value - self.initial_deposit
        
    def get_holdings(self):
        """
        Retorna un diccionario de las acciones actuales y sus cantidades.
        
        Returns:
            dict: Un diccionario con los símbolos y cantidades de acciones.
        """
        return self.holdings.copy()
        
    def get_transaction_history(self):
        """
        Retorna una lista de todas las transacciones realizadas por el usuario.
        
        Returns:
            list: Una lista de transacciones.
        """
        return self.transactions.copy()
        
    def _record_transaction(self, type, details):
        """
        Registra una transacción en el historial de transacciones de la cuenta.
        
        Args:
            type (str): El tipo de transacción (DEPOSIT, WITHDRAW, BUY, SELL).
            details (str): Los detalles de la transacción.
        """
        transaction = {
            "date": datetime.now().isoformat(),
            "type": type,
            "details": details,
            "balance": self.balance
        }
        
        self.transactions.append(transaction)