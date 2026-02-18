import gradio as gr
from accounts import Account

# Inicializar una cuenta para el demo
account = Account("demo_user")

def create_account(account_id):
    global account
    account = Account(account_id)
    return f"Cuenta creada: {account_id}"

def make_deposit(amount):
    try:
        amount = float(amount)
        account.deposit(amount)
        return f"Depósito exitoso. Nuevo saldo: ${account.balance:.2f}"
    except ValueError as e:
        return f"Error: {str(e)}"

def make_withdrawal(amount):
    try:
        amount = float(amount)
        if account.withdraw(amount):
            return f"Retiro exitoso. Nuevo saldo: ${account.balance:.2f}"
        else:
            return "Error: Fondos insuficientes para el retiro."
    except ValueError as e:
        return f"Error: {str(e)}"

def buy_stock(symbol, quantity):
    try:
        quantity = int(quantity)
        if account.buy_shares(symbol, quantity):
            return f"Compra exitosa de {quantity} acciones de {symbol}. Nuevo saldo: ${account.balance:.2f}"
        else:
            return "Error: Fondos insuficientes para la compra o símbolo no válido."
    except ValueError as e:
        return f"Error: {str(e)}"

def sell_stock(symbol, quantity):
    try:
        quantity = int(quantity)
        if account.sell_shares(symbol, quantity):
            return f"Venta exitosa de {quantity} acciones de {symbol}. Nuevo saldo: ${account.balance:.2f}"
        else:
            return "Error: No posees suficientes acciones para vender o símbolo no válido."
    except ValueError as e:
        return f"Error: {str(e)}"

def get_account_summary():
    portfolio_value = account.get_portfolio_value()
    profit_loss = account.get_profit_or_loss()
    
    summary = f"ID de Cuenta: {account.account_id}\n"
    summary += f"Saldo actual: ${account.balance:.2f}\n"
    summary += f"Valor del portafolio: ${portfolio_value:.2f}\n"
    summary += f"Valor total: ${(account.balance + portfolio_value):.2f}\n"
    summary += f"Depósito inicial: ${account.initial_deposit:.2f}\n"
    summary += f"Ganancia/Pérdida: ${profit_loss:.2f} "
    summary += f"({profit_loss / account.initial_deposit * 100:.2f}% del depósito inicial)" if account.initial_deposit > 0 else ""
    
    return summary

def get_current_holdings():
    holdings = account.get_holdings()
    
    if not holdings:
        return "No tienes acciones actualmente."
    
    result = "Acciones actuales:\n"
    for symbol, quantity in holdings.items():
        try:
            from accounts import get_share_price
            current_price = get_share_price(symbol)
            value = quantity * current_price
            result += f"{symbol}: {quantity} acciones - ${current_price:.2f} por acción - Valor total: ${value:.2f}\n"
        except ValueError:
            result += f"{symbol}: {quantity} acciones - Precio no disponible\n"
    
    return result

def get_transaction_history():
    transactions = account.get_transaction_history()
    
    if not transactions:
        return "No hay historial de transacciones."
    
    result = "Historial de Transacciones:\n"
    for i, transaction in enumerate(transactions, 1):
        date = transaction["date"].split("T")[0]
        time = transaction["date"].split("T")[1][:8]
        result += f"{i}. [{date} {time}] {transaction['type']}: {transaction['details']} - Saldo resultante: ${transaction['balance']:.2f}\n"
    
    return result

def get_stock_price(symbol):
    try:
        from accounts import get_share_price
        price = get_share_price(symbol)
        return f"Precio actual de {symbol}: ${price:.2f}"
    except ValueError as e:
        return f"Error: {str(e)}"

# Interfaz de Gradio
with gr.Blocks(title="Simulador de Trading") as demo:
    gr.Markdown("# Sistema de Gestión de Cuentas - Simulador de Trading")
    
    with gr.Tab("Cuenta"):
        with gr.Row():
            with gr.Column():
                account_id_input = gr.Textbox(label="ID de Cuenta", value="demo_user")
                create_account_btn = gr.Button("Crear Cuenta")
                
                deposit_input = gr.Number(label="Monto a Depositar")
                deposit_btn = gr.Button("Depositar")
                
                withdraw_input = gr.Number(label="Monto a Retirar")
                withdraw_btn = gr.Button("Retirar")
            
            account_output = gr.Textbox(label="Resultado", lines=5)
    
    with gr.Tab("Trading"):
        with gr.Row():
            with gr.Column():
                symbol_input = gr.Textbox(label="Símbolo de la Acción (AAPL, TSLA, GOOGL)", value="AAPL")
                quantity_input = gr.Number(label="Cantidad", value=1, precision=0)
                
                buy_btn = gr.Button("Comprar")
                sell_btn = gr.Button("Vender")
                
                check_price_btn = gr.Button("Consultar Precio")
            
            trading_output = gr.Textbox(label="Resultado", lines=5)
    
    with gr.Tab("Resumen"):
        refresh_summary_btn = gr.Button("Actualizar Resumen")
        summary_output = gr.Textbox(label="Resumen de la Cuenta", lines=10)
        
        refresh_holdings_btn = gr.Button("Ver Posiciones Actuales")
        holdings_output = gr.Textbox(label="Posiciones", lines=10)
        
        refresh_history_btn = gr.Button("Ver Historial de Transacciones")
        history_output = gr.Textbox(label="Historial", lines=15)
    
    # Eventos
    create_account_btn.click(create_account, inputs=[account_id_input], outputs=account_output)
    deposit_btn.click(make_deposit, inputs=[deposit_input], outputs=account_output)
    withdraw_btn.click(make_withdrawal, inputs=[withdraw_input], outputs=account_output)
    
    buy_btn.click(buy_stock, inputs=[symbol_input, quantity_input], outputs=trading_output)
    sell_btn.click(sell_stock, inputs=[symbol_input, quantity_input], outputs=trading_output)
    check_price_btn.click(get_stock_price, inputs=[symbol_input], outputs=trading_output)
    
    refresh_summary_btn.click(get_account_summary, inputs=[], outputs=summary_output)
    refresh_holdings_btn.click(get_current_holdings, inputs=[], outputs=holdings_output)
    refresh_history_btn.click(get_transaction_history, inputs=[], outputs=history_output)

if __name__ == "__main__":
    demo.launch()