from src.bot import DBAutomator

def main():
    # Defina headless=True se quiser rodar sem interface gráfica
    bot = DBAutomator(headless=False)
    bot.run()

if __name__ == "__main__":
    main()
