import asyncio
from dotenv import load_dotenv

from browser_use import Agent, Browser, BrowserProfile, ChatBrowserUse

load_dotenv()

# 👉 AJUSTE ESTE PATH PARA O QUE O `find` TE MOSTROU
CHROME_PATH = "/home/steff/.cache/ms-playwright/chromium-1200/chrome-linux64/chrome"


async def main():
    # Configura o browser para usar esse binário local
    profile = BrowserProfile(
        executable_path=CHROME_PATH,  # força usar esse chromium
        is_local=True,               # deixa explícito que é local
        headless=True,               # via SSH, sem janela gráfica
        keep_alive=False,            # fecha o browser ao final (pode mudar depois)
    )

    browser = Browser(browser_profile=profile)

    agent = Agent(
        task="Find the number of stars of the browser-use repository on GitHub",
        llm=ChatBrowserUse(),
        browser=browser,  # usamos o browser que acabamos de configurar
    )

    history = await agent.run()
    print("\n==== RESULTADO FINAL ====\n")
    print(history.final_result())


if __name__ == "__main__":
    asyncio.run(main())
